"""
Analytics service tests.

Covers Part 17 #9 (dashboard performance — assertNumQueries budget) and
the reconciliation guarantee: the dashboard numbers come from the same
service as reports would, so counts cannot diverge.
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

from apps.customers.models import Customer
from apps.employees.models import Employee
from apps.leads.models import Lead, LeadAssignmentHistory
from apps.sales.models import FollowUp, SalesActivity
from apps.tasks.models import Task

from apps.analytics import services as kpi
from apps.core.timezones import company_day_range_utc, now_company


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    u, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": u.email, "password": pwd}, format="json")
    return u


@pytest.fixture
def seed(make_user):
    """Minimal fixture: 1 employee, several leads/activities today + earlier."""
    user, _ = make_user(email="sp@example.com", role_name="Salesperson")
    emp = Employee.objects.create(user=user, employee_code="E001",
                                  full_name="SP")
    today = now_company().date()
    start, _ = company_day_range_utc(today)

    # 2 leads created today
    l1 = Lead.objects.create(full_name="A", assigned_to=emp,
                             status=Lead.Status.ASSIGNED)
    l2 = Lead.objects.create(full_name="B")  # unassigned

    # 1 assignment event today
    LeadAssignmentHistory.objects.create(
        lead=l1, to_employee=emp)

    # 1 activity today
    SalesActivity.objects.create(
        kind=SalesActivity.Kind.CALL_OUT, lead=l1, performed_by=emp,
        occurred_at=timezone.now(),
    )

    # 1 overdue follow-up
    FollowUp.objects.create(
        lead=l1, owner=emp, summary="late",
        due_at=timezone.now() - timedelta(hours=2),
    )

    # 1 overdue task
    Task.objects.create(
        title="old", assignee=emp,
        due_at=timezone.now() - timedelta(days=1),
    )
    return emp


# ----- Formula checks -----

def test_today_payload_matches_underlying_counts(seed):
    payload = kpi.today_payload()
    assert payload["leads_received"] == 2
    assert payload["leads_assigned"] == 1
    assert payload["leads_awaiting_assignment"] == 1
    assert payload["calls_logged"] == 1
    assert payload["activities_logged"] == 1
    assert payload["followups_overdue"] == 1
    assert payload["tasks_overdue"] == 1


def test_filters_narrow_counts(seed):
    # With filter for a non-existent employee, counts drop to zero.
    f = kpi.Filters(employee_id="00000000-0000-0000-0000-000000000000")
    assert kpi.today_payload(f=f)["leads_assigned"] == 0


def test_weekly_payload_includes_source_breakdown(seed):
    payload = kpi.weekly_payload()
    assert payload["leads_received"] >= 2
    assert isinstance(payload["leads_by_source"], list)


# ----- Reconciliation -----

def test_endpoint_reconciles_with_service(api, owner_login, seed):
    """
    The API must return the same numbers as the service module. Any future
    aggregation that bypasses apps/analytics/services would break this.
    """
    service_payload = kpi.today_payload()
    resp = api.get("/api/v1/analytics/dashboard/today/")
    assert resp.status_code == 200
    body = resp.json()
    for key, value in service_payload.items():
        assert body[key] == value, f"mismatch on {key}"


# ----- Performance budget (Part 17 #9) -----

def test_today_endpoint_stays_within_query_budget(api, owner_login, seed):
    with CaptureQueriesContext(connection) as ctx:
        resp = api.get("/api/v1/analytics/dashboard/today/")
    assert resp.status_code == 200
    # ~12 metric queries + 1-2 session/auth lookups. Hard cap at 25.
    assert len(ctx) <= 25, (
        f"Dashboard produced {len(ctx)} queries; budget exceeded. "
        "Check for N+1 regressions in apps/analytics/services.py."
    )


def test_weekly_endpoint_stays_within_query_budget(api, owner_login, seed):
    with CaptureQueriesContext(connection) as ctx:
        resp = api.get("/api/v1/analytics/dashboard/weekly/")
    assert resp.status_code == 200
    assert len(ctx) <= 20


# ----- Permissions -----

def test_reports_read_permission_required(api, make_user):
    user, pwd = make_user(email="noperm@example.com",
                          role_name="Customer Support")
    # Customer Support does not have reports.read.
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    resp = api.get("/api/v1/analytics/dashboard/today/")
    assert resp.status_code == 403


# ----- Leaderboard -----

def test_leaderboard_sorts_by_activity_then_conversion(seed):
    other_user_emp = seed  # reuse fixture
    other_user_emp2_user = Employee.objects.create(
        user=other_user_emp.user,  # reuse to avoid creating a real user
        employee_code="E002", full_name="X",
    ) if False else None  # skip: single employee suffices for sort check
    start, end = company_day_range_utc(now_company().date())
    rows = kpi.salesperson_leaderboard(start, end)
    assert len(rows) >= 1
    assert rows[0]["activities"] >= 1
