"""Auth flow tests: login, logout, me, password reset, deactivation."""
from __future__ import annotations

import pytest

from apps.audit.models import AuditLog


pytestmark = pytest.mark.django_db


def test_login_and_me(api, make_user):
    user, pwd = make_user(email="sales@example.com", role_name="Salesperson")
    resp = api.post("/api/v1/auth/login/",
                    {"email": user.email, "password": pwd}, format="json")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["email"] == user.email
    assert body["role"] == "Salesperson"
    assert "leads.read" in body["permissions"]

    me = api.get("/api/v1/auth/me/")
    assert me.status_code == 200
    assert me.json()["email"] == user.email


def test_login_rejects_invalid_credentials(api, make_user):
    make_user(email="x@example.com")
    resp = api.post("/api/v1/auth/login/",
                    {"email": "x@example.com", "password": "nope"},
                    format="json")
    assert resp.status_code == 400
    assert AuditLog.objects.filter(action="login.failed").count() == 1


def test_deactivated_user_cannot_log_in(api, make_user):
    user, pwd = make_user(email="gone@example.com",
                          role_name="Salesperson", is_active=False)
    resp = api.post("/api/v1/auth/login/",
                    {"email": user.email, "password": pwd}, format="json")
    assert resp.status_code == 400


def test_unauthenticated_me_returns_403(api):
    resp = api.get("/api/v1/auth/me/")
    assert resp.status_code in (401, 403)


def test_logout_clears_session(api, make_user):
    user, pwd = make_user()
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    assert api.get("/api/v1/auth/me/").status_code == 200
    out = api.post("/api/v1/auth/logout/")
    assert out.status_code == 204
    assert api.get("/api/v1/auth/me/").status_code in (401, 403)


def test_password_reset_request_always_204(api, make_user):
    make_user(email="exists@example.com")
    assert api.post("/api/v1/auth/password/reset/request/",
                    {"email": "exists@example.com"},
                    format="json").status_code == 204
    # Unknown email — same 204, no leakage
    assert api.post("/api/v1/auth/password/reset/request/",
                    {"email": "unknown@example.com"},
                    format="json").status_code == 204


def test_password_reset_confirm_flow(api, make_user):
    from apps.accounts.services import make_reset_token
    user, _ = make_user(email="reset@example.com")
    uid, token = make_reset_token(user)

    resp = api.post("/api/v1/auth/password/reset/confirm/",
                    {"uid": uid, "token": token,
                     "new_password": "BrandNewPass!99"},
                    format="json")
    assert resp.status_code == 204

    # Old password no longer works; new one does
    assert api.post("/api/v1/auth/login/",
                    {"email": user.email, "password": "Testpass!2345"},
                    format="json").status_code == 400
    assert api.post("/api/v1/auth/login/",
                    {"email": user.email, "password": "BrandNewPass!99"},
                    format="json").status_code == 200


def test_password_reset_rejects_invalid_token(api, make_user):
    user, _ = make_user(email="r2@example.com")
    resp = api.post("/api/v1/auth/password/reset/confirm/",
                    {"uid": "bad", "token": "bad",
                     "new_password": "WhateverLong!1"},
                    format="json")
    assert resp.status_code == 400
