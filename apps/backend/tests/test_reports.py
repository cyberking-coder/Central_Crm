"""Phase 8 — reports + public lead capture."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as dt_tz
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.analytics import services as kpi
from apps.core.timezones import company_day_range_utc, company_week_range_utc
from apps.customers.models import Customer
from apps.employees.models import Employee
from apps.finance.models import Payment
from apps.finance.services.payments import record_payment
from apps.leads.models import Lead
from apps.marketing.models import Campaign, LeadSource


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    u, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": u.email, "password": pwd}, format="json")
    return u


@pytest.fixture
def seeded():
    website = LeadSource.objects.get(slug="website")
    facebook = LeadSource.objects.get(slug="facebook")
    campaign = Campaign.objects.create(
        name="Diwali 2026", source=facebook,
        utm_campaign="diwali_2026",
        spend=Decimal("1000.00"), currency="INR",
    )

    # 2 website leads: 1 converted
    cust = Customer.objects.create(full_name="C1", source=website)
    l1 = Lead.objects.create(full_name="W1", source=website,
                             status=Lead.Status.CONVERTED,
                             converted_customer=cust,
                             converted_at=timezone.now())
    Lead.objects.create(full_name="W2", source=website,
                        status=Lead.Status.NEW)

    # 3 facebook leads: 1 converted
    cust2 = Customer.objects.create(full_name="C2", source=facebook)
    Lead.objects.create(full_name="F1", source=facebook, campaign=campaign,
                        status=Lead.Status.CONVERTED,
                        converted_customer=cust2,
                        converted_at=timezone.now())
    Lead.objects.create(full_name="F2", source=facebook, campaign=campaign,
                        status=Lead.Status.QUALIFIED)
    Lead.objects.create(full_name="F3", source=facebook, campaign=campaign,
                        status=Lead.Status.LOST)

    # Revenue
    record_payment(customer=cust, amount="500.00", currency="INR",
                   payment_date=date.today(), method=Payment.Method.CASH)
    record_payment(customer=cust2, amount="3000.00", currency="INR",
                   payment_date=date.today(), method=Payment.Method.CASH)
    return {"website": website, "facebook": facebook, "campaign": campaign}


# ----- Source performance -----

def test_source_report_counts(seeded):
    start, end = company_week_range_utc(timezone.now().date())
    rows = kpi.source_performance_report(start, end)
    by_source = {r["source"]: r for r in rows}
    w = by_source["Website"]
    assert w["leads"] == 2
    assert w["converted"] == 1
    assert w["conversion_pct"] == 50.0
    # Revenue tied to converted customer with source=Website.
    assert Decimal(w["attributed_revenue"]) == Decimal("500.00")

    f = by_source["Facebook"]
    assert f["leads"] == 3
    assert f["converted"] == 1
    assert Decimal(f["attributed_revenue"]) == Decimal("3000.00")


# ----- Campaign performance (CPL + ROI) -----

def test_campaign_report_computes_cpl_and_roi(seeded):
    start, end = company_week_range_utc(timezone.now().date())
    rows = kpi.campaign_performance_report(start, end)
    row = next(r for r in rows if r["campaign"] == "Diwali 2026")
    assert row["leads"] == 3
    assert row["converted"] == 1
    assert row["spend"] == "1000.00"
    # Revenue = 3000, spend = 1000. CPL = 1000/3 = 333.33. ROI = 200%.
    assert row["cost_per_lead"] == "333.33"
    assert row["roi_pct"] == 200.0


# ----- Funnel -----

def test_funnel_counts(seeded):
    start, end = company_week_range_utc(timezone.now().date())
    f = kpi.conversion_funnel(start, end)
    assert f["leads"] == 5
    assert f["converted"] == 2
    assert f["qualified"] == 3  # QUALIFIED + CONVERTED
    assert f["lost"] == 1


# ----- Report endpoints + CSV export -----

def test_source_report_endpoint_reconciles(api, owner_login, seeded):
    start, end = company_week_range_utc(timezone.now().date())
    service_rows = kpi.source_performance_report(start, end)
    resp = api.get(f"/api/v1/analytics/reports/sources/?from="
                   f"{start.date().isoformat()}&to="
                   f"{(end.date() - timedelta(days=1)).isoformat()}")
    assert resp.status_code == 200
    api_rows = resp.json()["rows"]
    # Same set of (source, leads) pairs.
    assert sorted((r["source"], r["leads"]) for r in api_rows) == \
           sorted((r["source"], r["leads"]) for r in service_rows)


def test_export_csv_runs_through_sanitiser(api, owner_login, seeded):
    resp = api.get("/api/v1/analytics/reports/sources/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")


def test_reports_require_reports_read(api, make_user, seeded):
    user, pwd = make_user(email="noperm@example.com",
                          role_name="Customer Support")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    assert api.get("/api/v1/analytics/reports/sources/").status_code == 403


# ----- Public lead capture -----

def test_public_capture_creates_lead_and_links_campaign(api):
    LeadSource.objects.get_or_create(slug="facebook",
                                      defaults={"name": "Facebook"})
    c = Campaign.objects.create(
        name="Public Promo",
        source=LeadSource.objects.get(slug="facebook"),
        utm_campaign="public_promo", is_active=True,
    )
    resp = api.post("/api/v1/leads/public/", {
        "full_name": "Walk-in",
        "email": "walkin@example.com",
        "utm_source": "facebook",
        "utm_campaign": "public_promo",
    }, format="json")
    assert resp.status_code == 201, resp.content
    lead_id = resp.json()["lead_id"]
    lead = Lead.objects.get(pk=lead_id)
    assert lead.source.slug == "facebook"
    assert lead.campaign_id == c.id


def test_public_capture_dedupes_silently(api):
    LeadSource.objects.get_or_create(slug="website",
                                      defaults={"name": "Website"})
    Lead.objects.create(full_name="Dup", email="d@example.com",
                        email_normalised="d@example.com")
    resp = api.post("/api/v1/leads/public/", {
        "full_name": "Dup Again", "email": "D@example.com",
    }, format="json")
    assert resp.status_code == 200
    # Only the original row remains.
    assert Lead.objects.filter(email_normalised="d@example.com").count() == 1


def test_public_capture_no_auth_required(api):
    LeadSource.objects.get_or_create(slug="website",
                                      defaults={"name": "Website"})
    resp = api.post("/api/v1/leads/public/",
                    {"full_name": "No Auth"}, format="json")
    assert resp.status_code == 201
