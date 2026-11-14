"""Webinars: capacity, duplicates, attendance, stats, permissions."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.employees.models import Employee
from apps.webinars.models import Webinar, WebinarAttendance, WebinarRegistration
from apps.webinars.services.registration import (
    RegistrationError,
    register_for_webinar,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    u, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": u.email, "password": pwd}, format="json")
    return u


@pytest.fixture
def support_login(api, make_user):
    u, pwd = make_user(email="s@example.com", role_name="Customer Support")
    api.post("/api/v1/auth/login/",
             {"email": u.email, "password": pwd}, format="json")
    return u


@pytest.fixture
def webinar():
    return Webinar.objects.create(
        title="Intro", start_at=timezone.now() + timedelta(days=1),
        end_at=timezone.now() + timedelta(days=1, hours=1),
        registration_limit=2,
    )


# ----- Capacity -----

def test_capacity_blocks_third_registration(webinar):
    register_for_webinar(webinar=webinar, full_name="A", email="a@e.com")
    register_for_webinar(webinar=webinar, full_name="B", email="b@e.com")
    with pytest.raises(RegistrationError):
        register_for_webinar(webinar=webinar, full_name="C", email="c@e.com")


def test_cancelled_registration_frees_capacity(webinar):
    r1 = register_for_webinar(webinar=webinar, full_name="A", email="a@e.com")
    register_for_webinar(webinar=webinar, full_name="B", email="b@e.com")
    r1.status = WebinarRegistration.Status.CANCELLED
    r1.save()
    r3 = register_for_webinar(webinar=webinar, full_name="C", email="c@e.com")
    assert r3.pk != r1.pk


def test_unlimited_capacity_allows_many():
    w = Webinar.objects.create(
        title="Open", registration_limit=0,
        start_at=timezone.now(), end_at=timezone.now() + timedelta(hours=1))
    for i in range(5):
        register_for_webinar(webinar=w, full_name=f"P{i}",
                             email=f"p{i}@e.com")
    assert w.registrations.count() == 5


# ----- Duplicates -----

def test_duplicate_email_rejected(webinar):
    register_for_webinar(webinar=webinar, full_name="A",
                         email="Dup@Example.COM")
    with pytest.raises(RegistrationError):
        register_for_webinar(webinar=webinar, full_name="A2",
                             email="dup@example.com")


def test_duplicate_phone_rejected(webinar):
    register_for_webinar(webinar=webinar, full_name="A",
                         phone="+1 (555) 111-2222")
    with pytest.raises(RegistrationError):
        register_for_webinar(webinar=webinar, full_name="A2",
                             phone="5551112222")


def test_same_contact_across_webinars_allowed():
    w1 = Webinar.objects.create(
        title="W1", start_at=timezone.now(),
        end_at=timezone.now() + timedelta(hours=1))
    w2 = Webinar.objects.create(
        title="W2", start_at=timezone.now(),
        end_at=timezone.now() + timedelta(hours=1))
    register_for_webinar(webinar=w1, full_name="X", email="x@e.com")
    register_for_webinar(webinar=w2, full_name="X", email="x@e.com")


# ----- API -----

def test_create_webinar_requires_manage_permission(api, support_login):
    resp = api.post("/api/v1/webinars/",
                    {"title": "W", "start_at": "2026-12-01T10:00:00Z",
                     "end_at": "2026-12-01T11:00:00Z"}, format="json")
    assert resp.status_code == 403


def test_create_webinar_validates_end_after_start(api, owner_login):
    resp = api.post("/api/v1/webinars/",
                    {"title": "Bad", "start_at": "2026-12-01T11:00:00Z",
                     "end_at": "2026-12-01T10:00:00Z"}, format="json")
    assert resp.status_code == 400


def test_register_endpoint_returns_201(api, owner_login, webinar):
    resp = api.post(f"/api/v1/webinars/{webinar.pk}/register/",
                    {"full_name": "P1", "email": "p1@e.com"},
                    format="json")
    assert resp.status_code == 201


def test_register_capacity_returns_400(api, owner_login, webinar):
    for i in range(2):
        api.post(f"/api/v1/webinars/{webinar.pk}/register/",
                 {"full_name": f"P{i}", "email": f"p{i}@e.com"},
                 format="json")
    r = api.post(f"/api/v1/webinars/{webinar.pk}/register/",
                 {"full_name": "overflow", "email": "x@e.com"},
                 format="json")
    assert r.status_code == 400


# ----- Attendance + stats -----

def test_stats_endpoint_reconciles(api, owner_login, webinar):
    r1 = register_for_webinar(webinar=webinar, full_name="A", email="a@e.com")
    r2 = register_for_webinar(webinar=webinar, full_name="B", email="b@e.com")
    r1.attendance.status = WebinarAttendance.Status.ATTENDED
    r1.attendance.save()
    r2.attendance.status = WebinarAttendance.Status.ABSENT
    r2.attendance.save()
    resp = api.get(f"/api/v1/webinars/{webinar.pk}/stats/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["registrations_total"] == 2
    assert body["attended"] == 1
    assert body["absent"] == 1
    assert body["attendance_rate_pct"] == 50.0


def test_attendance_update_records_audit(api, owner_login, webinar):
    reg = register_for_webinar(webinar=webinar, full_name="A", email="a@e.com")
    resp = api.patch(f"/api/v1/webinars/attendance/{reg.attendance.pk}/",
                     {"status": "attended"}, format="json")
    assert resp.status_code == 200
    reg.attendance.refresh_from_db()
    assert reg.attendance.status == "attended"
    from apps.audit.models import AuditLog
    assert AuditLog.objects.filter(action="webinar.attendance.updated").exists()
