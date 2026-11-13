"""Sales activities + follow-ups: scoping, side effects, overdue sweep."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.customers.models import Customer, CustomerTimelineEvent
from apps.employees.models import Employee
from apps.leads.models import Lead
from apps.notifications.models import Notification
from apps.sales.models import FollowUp, SalesActivity


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    user, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    return user


@pytest.fixture
def salesperson(make_user):
    user, pwd = make_user(email="sp@example.com", role_name="Salesperson")
    emp = Employee.objects.create(user=user, employee_code="E001",
                                  full_name="SP")
    return user, pwd, emp


def test_activity_requires_lead_or_customer(api, owner_login):
    resp = api.post("/api/v1/sales/activities/",
                    {"kind": "call_out", "outcome": "ok"}, format="json")
    assert resp.status_code == 400


def test_activity_on_customer_adds_timeline(api, owner_login):
    cust = Customer.objects.create(full_name="C")
    resp = api.post("/api/v1/sales/activities/",
                    {"kind": "call_out", "customer": str(cust.pk),
                     "outcome": "spoke"}, format="json")
    assert resp.status_code == 201
    assert cust.timeline.count() == 1


def test_activity_on_lead_updates_last_contacted(api, owner_login):
    lead = Lead.objects.create(full_name="L")
    assert lead.last_contacted_at is None
    api.post("/api/v1/sales/activities/",
             {"kind": "call_out", "lead": str(lead.pk)}, format="json")
    lead.refresh_from_db()
    assert lead.last_contacted_at is not None


def test_salesperson_sees_only_own_activities(api, make_user, salesperson, owner_login):
    sp_user, sp_pwd, sp_emp = salesperson
    other_user, _ = make_user(email="o2@example.com", role_name="Salesperson")
    other_emp = Employee.objects.create(user=other_user, employee_code="E2",
                                         full_name="O2")
    lead = Lead.objects.create(full_name="L")
    SalesActivity.objects.create(kind="call_out", lead=lead, performed_by=sp_emp)
    SalesActivity.objects.create(kind="call_out", lead=lead, performed_by=other_emp)
    api.post("/api/v1/auth/logout/")
    api.post("/api/v1/auth/login/",
             {"email": sp_user.email, "password": sp_pwd}, format="json")
    resp = api.get("/api/v1/sales/activities/")
    assert resp.json()["count"] == 1


def test_followup_complete_updates_status(api, owner_login, salesperson):
    _, _, emp = salesperson
    lead = Lead.objects.create(full_name="L")
    fu = FollowUp.objects.create(lead=lead, owner=emp,
                                  due_at=timezone.now() + timedelta(days=1),
                                  summary="call back")
    resp = api.post(f"/api/v1/sales/followups/{fu.pk}/complete/")
    assert resp.status_code == 200
    fu.refresh_from_db()
    assert fu.status == "done"
    assert fu.completed_at is not None


def test_sweep_overdue_followups_emits_and_dedupes(owner_login, salesperson):
    from apps.sales.services.followups import sweep_overdue_followups
    _, _, emp = salesperson
    lead = Lead.objects.create(full_name="L")
    FollowUp.objects.create(
        lead=lead, owner=emp,
        due_at=timezone.now() - timedelta(hours=2),
        summary="late",
    )
    assert sweep_overdue_followups() == 1
    assert sweep_overdue_followups() == 0  # dedup


def test_lead_assignment_notifies_assignee(api, owner_login, salesperson):
    _, _, emp = salesperson
    lead = Lead.objects.create(full_name="L")
    api.post(f"/api/v1/leads/{lead.pk}/assign/",
             {"employee_id": str(emp.pk)}, format="json")
    assert Notification.objects.filter(
        recipient=emp.user, kind="lead_assigned").count() == 1
