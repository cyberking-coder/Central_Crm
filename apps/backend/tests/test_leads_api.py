"""End-to-end lead API: CRUD, permissions, assignment, conversion, CSV."""
from __future__ import annotations

import io

import pytest

from apps.audit.models import AuditLog
from apps.customers.models import Customer
from apps.employees.models import Employee
from apps.leads.models import Lead, LeadAssignmentHistory, LeadStatusHistory


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner(api, make_user):
    user, pwd = make_user(email="owner@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    return user


@pytest.fixture
def salesperson(make_user):
    user, pwd = make_user(email="sp@example.com", role_name="Salesperson")
    # Attach an Employee profile so the salesperson scoping works.
    employee = Employee.objects.create(
        user=user, employee_code="E001", full_name="Sales Person")
    return user, pwd, employee


@pytest.fixture
def support(make_user):
    user, pwd = make_user(email="sup@example.com", role_name="Customer Support")
    return user, pwd


def _login(api, email, password):
    api.post("/api/v1/auth/login/",
             {"email": email, "password": password}, format="json")


# ----- CRUD + permissions -----

def test_owner_can_create_lead(api, owner):
    resp = api.post("/api/v1/leads/",
                    {"full_name": "Alice", "phone": "+91 999 888 7777",
                     "email": "alice@example.com"}, format="json")
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["full_name"] == "Alice"
    assert body["status"] == "new"
    lead = Lead.objects.get(pk=body["id"])
    assert lead.phone_normalised == "919998887777"
    assert lead.email_normalised == "alice@example.com"


def test_support_cannot_create_lead(api, support):
    _login(api, support[0].email, support[1])
    resp = api.post("/api/v1/leads/",
                    {"full_name": "Alice"}, format="json")
    assert resp.status_code == 403


def test_salesperson_sees_only_assigned_leads(api, owner, salesperson):
    sp_user, sp_pwd, sp_emp = salesperson
    Lead.objects.create(full_name="Mine", assigned_to=sp_emp)
    Lead.objects.create(full_name="Not mine")

    api.post("/api/v1/auth/logout/")
    _login(api, sp_user.email, sp_pwd)

    resp = api.get("/api/v1/leads/")
    assert resp.status_code == 200
    names = [r["full_name"] for r in resp.json()["results"]]
    assert names == ["Mine"]


def test_unauthenticated_cannot_list(api):
    assert api.get("/api/v1/leads/").status_code in (401, 403)


# ----- Assignment -----

def test_assign_lead_records_history_and_audit(api, owner, salesperson):
    sp_user, _, sp_emp = salesperson
    lead = Lead.objects.create(full_name="Bob")
    resp = api.post(f"/api/v1/leads/{lead.pk}/assign/",
                    {"employee_id": str(sp_emp.pk), "reason": "round-robin"},
                    format="json")
    assert resp.status_code == 200
    lead.refresh_from_db()
    assert lead.assigned_to_id == sp_emp.pk
    assert lead.status == "assigned"
    assert LeadAssignmentHistory.objects.filter(lead=lead).count() == 1
    assert AuditLog.objects.filter(action="lead.assigned").exists()


def test_assign_rejects_unknown_employee(api, owner):
    lead = Lead.objects.create(full_name="Bob")
    resp = api.post(f"/api/v1/leads/{lead.pk}/assign/",
                    {"employee_id": "00000000-0000-0000-0000-000000000000"},
                    format="json")
    assert resp.status_code == 400


# ----- Conversion -----

def test_convert_creates_customer_and_links_back(api, owner):
    lead = Lead.objects.create(full_name="Carol", phone="999",
                               phone_normalised="999",
                               email="c@e.com", email_normalised="c@e.com")
    resp = api.post(f"/api/v1/leads/{lead.pk}/convert/")
    assert resp.status_code == 201
    cust_id = resp.json()["customer_id"]
    lead.refresh_from_db()
    assert str(lead.converted_customer_id) == cust_id
    assert lead.status == "converted"
    customer = Customer.objects.get(pk=cust_id)
    assert customer.full_name == "Carol"
    assert customer.timeline.count() == 1
    assert LeadStatusHistory.objects.filter(
        lead=lead, to_status="converted").exists()


def test_convert_twice_rejected(api, owner):
    lead = Lead.objects.create(full_name="Dan")
    api.post(f"/api/v1/leads/{lead.pk}/convert/")
    resp = api.post(f"/api/v1/leads/{lead.pk}/convert/")
    assert resp.status_code == 400


def test_convert_lost_lead_rejected(api, owner):
    lead = Lead.objects.create(full_name="Eve", status=Lead.Status.LOST)
    resp = api.post(f"/api/v1/leads/{lead.pk}/convert/")
    assert resp.status_code == 400


# ----- Duplicates -----

def test_duplicates_action_matches_on_phone(api, owner):
    Lead.objects.create(full_name="Fin", phone="+1 (555) 123-4567",
                        phone_normalised="15551234567")
    resp = api.get("/api/v1/leads/duplicates/?phone=5551234567")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ----- CSV export -----

def test_export_csv_is_sanitised(api, owner):
    Lead.objects.create(full_name="=1+1", email="ok@e.com",
                        email_normalised="ok@e.com")
    resp = api.get("/api/v1/leads/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")
    body = resp.content.decode("utf-8")
    assert "'=1+1" in body  # Part 17 #10 sanitiser applied


def test_export_requires_leads_export_permission(api, support):
    _login(api, support[0].email, support[1])
    resp = api.get("/api/v1/leads/export/")
    assert resp.status_code == 403


# ----- CSV import -----

def test_import_csv_creates_leads_and_skips_duplicates(api, owner):
    Lead.objects.create(full_name="Existing", phone="111",
                        phone_normalised="111")
    csv = (
        "full_name,phone,email\n"
        "New Person,+1 555 111 2222,new@e.com\n"
        "Dup Person,111,dup@e.com\n"
        ",nope,missing@e.com\n"
    )
    file = io.BytesIO(csv.encode("utf-8"))
    file.name = "leads.csv"
    resp = api.post("/api/v1/leads/import/",
                    {"file": file}, format="multipart")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["created"] == 1
    assert body["duplicates_skipped"] == 1
    assert len(body["failed"]) == 1


def test_import_rejects_missing_required_column(api, owner):
    csv = "name,email\nAlice,a@e.com\n"
    file = io.BytesIO(csv.encode("utf-8"))
    file.name = "leads.csv"
    resp = api.post("/api/v1/leads/import/",
                    {"file": file}, format="multipart")
    assert resp.status_code == 400


# ----- History -----

def test_history_endpoint_returns_assignment_and_status(api, owner, salesperson):
    _, _, sp_emp = salesperson
    lead = Lead.objects.create(full_name="Hank")
    api.post(f"/api/v1/leads/{lead.pk}/assign/",
             {"employee_id": str(sp_emp.pk)}, format="json")
    api.patch(f"/api/v1/leads/{lead.pk}/",
              {"status": "contacted"}, format="json")
    resp = api.get(f"/api/v1/leads/{lead.pk}/history/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["assignments"]) == 1
    assert len(data["statuses"]) == 1
