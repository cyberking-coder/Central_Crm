"""Razorpay webhook idempotency + email adapter + status endpoint."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from decimal import Decimal

import pytest
from django.core import mail

from apps.customers.models import Customer
from apps.finance.models import Payment, WebhookEvent


pytestmark = pytest.mark.django_db


RAZORPAY_SECRET = "test_secret_xyz"


@pytest.fixture(autouse=True)
def _razorpay_secret(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_SECRET)


def _sign(body: bytes) -> str:
    return hmac.new(RAZORPAY_SECRET.encode(), body,
                    hashlib.sha256).hexdigest()


def _rzp_payload(event_id: str, event_type: str, *,
                 amount_paise: int = 50000, email: str = "a@e.com"):
    return {
        "id": event_id,
        "event": event_type,
        "payload": {"payment": {"entity": {
            "id": f"pay_{event_id}", "amount": amount_paise,
            "currency": "INR", "email": email, "contact": "+919999999999",
        }}},
    }


def test_invalid_signature_rejected(api):
    body = json.dumps(_rzp_payload("evt_1", "payment.captured")).encode()
    resp = api.post(
        "/api/v1/integrations/webhooks/razorpay/",
        data=body, content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE="bad",
    )
    assert resp.status_code == 400
    assert WebhookEvent.objects.count() == 0  # dedup key not burned


def test_payment_captured_records_payment_and_dedupes():
    Customer.objects.create(full_name="A", email="a@e.com",
                             email_normalised="a@e.com")
    body = json.dumps(_rzp_payload("evt_cap_1", "payment.captured")).encode()
    sig = _sign(body)

    from rest_framework.test import APIClient
    c = APIClient()

    r1 = c.post("/api/v1/integrations/webhooks/razorpay/",
                 data=body, content_type="application/json",
                 HTTP_X_RAZORPAY_SIGNATURE=sig)
    assert r1.status_code == 200
    assert r1.json()["duplicate"] is False
    assert Payment.objects.filter(
        method=Payment.Method.GATEWAY).count() == 1

    # Replay: same signature, same body.
    r2 = c.post("/api/v1/integrations/webhooks/razorpay/",
                 data=body, content_type="application/json",
                 HTTP_X_RAZORPAY_SIGNATURE=sig)
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True
    assert Payment.objects.filter(
        method=Payment.Method.GATEWAY).count() == 1  # still one


def test_unknown_event_type_stored_but_skipped():
    body = json.dumps(_rzp_payload("evt_unk", "payment.something_new")).encode()
    sig = _sign(body)
    from rest_framework.test import APIClient
    c = APIClient()
    r = c.post("/api/v1/integrations/webhooks/razorpay/",
                data=body, content_type="application/json",
                HTTP_X_RAZORPAY_SIGNATURE=sig)
    assert r.status_code == 200
    ev = WebhookEvent.objects.get(provider_event_id="evt_unk")
    assert ev.status == WebhookEvent.Status.PROCESSED
    assert Payment.objects.count() == 0


def test_payment_entity_without_matching_customer_is_skipped():
    body = json.dumps(_rzp_payload("evt_nocust", "payment.captured",
                                    email="nobody@example.com")).encode()
    sig = _sign(body)
    from rest_framework.test import APIClient
    c = APIClient()
    r = c.post("/api/v1/integrations/webhooks/razorpay/",
                data=body, content_type="application/json",
                HTTP_X_RAZORPAY_SIGNATURE=sig)
    assert r.status_code == 200
    body_json = r.json()
    assert body_json["result"]["skipped"] == "no_customer_match"
    assert Payment.objects.count() == 0


# ----- Email adapter -----

def test_email_adapter_sends_with_locmem_backend(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    from apps.integrations.adapters.email_adapter import send_html_email
    send_html_email(to="x@e.com", subject="Hi",
                    text_body="plain", html_body="<b>rich</b>")
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["x@e.com"]
    assert msg.subject == "Hi"
    assert "plain" in msg.body


# ----- Status endpoint -----

def test_status_endpoint_requires_permission(api, make_user):
    user, pwd = make_user(email="sp@example.com", role_name="Salesperson")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    resp = api.get("/api/v1/integrations/status/")
    assert resp.status_code == 403


def test_status_endpoint_reports_configured_flag(api, make_user):
    user, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    resp = api.get("/api/v1/integrations/status/")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["integrations"]]
    assert "razorpay" in names and "email" in names and "whatsapp" in names
    rzp = next(r for r in resp.json()["integrations"] if r["name"] == "razorpay")
    assert rzp["configured"] is True  # monkeypatched by _razorpay_secret
