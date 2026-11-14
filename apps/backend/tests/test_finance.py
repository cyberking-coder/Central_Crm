"""
Finance tests.

Covers Part 17 #2 (centralised money math, dashboard↔service reconciliation),
#4 (webhook idempotency), and payment/refund invariants.
"""
from __future__ import annotations

from datetime import date, datetime, timezone as dt_tz
from decimal import Decimal

import pytest

from apps.customers.models import Customer
from apps.finance.models import Invoice, Payment, Refund, WebhookEvent
from apps.finance.services.invoices import (
    create_invoice,
    issue_invoice,
    recompute_invoice_status,
    void_invoice,
)
from apps.finance.services.payments import (
    PaymentError,
    record_payment,
    record_refund,
)
from apps.finance.services.webhooks import ingest_webhook_event


pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_login(api, make_user):
    u, pwd = make_user(email="o@example.com", role_name="Company Owner")
    api.post("/api/v1/auth/login/",
             {"email": u.email, "password": pwd}, format="json")
    return u


@pytest.fixture
def customer():
    return Customer.objects.create(full_name="Alice")


# ----- Invoice math -----

def test_invoice_computes_totals_server_side(customer):
    inv = create_invoice(
        customer=customer,
        items=[
            {"description": "Widget", "quantity": 2, "unit_price": "100.00",
             "tax_rate": "18.000"},
            {"description": "Gadget", "quantity": 1, "unit_price": "50.00"},
        ],
    )
    assert inv.subtotal == Decimal("250.00")
    assert inv.tax == Decimal("36.00")        # 18% of 200
    assert inv.discount == Decimal("0.00")
    assert inv.total == Decimal("286.00")


def test_invoice_discount_cannot_go_negative(customer):
    inv = create_invoice(
        customer=customer,
        items=[{"description": "x", "quantity": 1, "unit_price": "10.00"}],
        discount="100.00",
    )
    assert inv.total == Decimal("0.00")


def test_invoice_number_is_sequential(customer):
    i1 = create_invoice(customer=customer,
                        items=[{"description": "a", "quantity": 1,
                                "unit_price": "10.00"}])
    i2 = create_invoice(customer=customer,
                        items=[{"description": "b", "quantity": 1,
                                "unit_price": "10.00"}])
    n1 = int(i1.number.split("-")[-1])
    n2 = int(i2.number.split("-")[-1])
    assert n2 == n1 + 1


# ----- Payments + invoice status -----

def test_full_payment_marks_invoice_paid(customer):
    inv = create_invoice(customer=customer,
                        items=[{"description": "x", "quantity": 1,
                                "unit_price": "100.00"}])
    issue_invoice(invoice=inv)
    record_payment(customer=customer, invoice=inv,
                   amount="100.00", currency=inv.currency,
                   payment_date=date.today(),
                   method=Payment.Method.CASH)
    inv.refresh_from_db()
    assert inv.status == Invoice.Status.PAID


def test_partial_payment_marks_invoice_partially_paid(customer):
    inv = create_invoice(customer=customer,
                        items=[{"description": "x", "quantity": 1,
                                "unit_price": "100.00"}])
    issue_invoice(invoice=inv)
    record_payment(customer=customer, invoice=inv,
                   amount="40.00", currency=inv.currency,
                   payment_date=date.today(),
                   method=Payment.Method.CASH)
    inv.refresh_from_db()
    assert inv.status == Invoice.Status.PARTIALLY_PAID


def test_duplicate_transaction_reference_rejected(customer):
    record_payment(customer=customer, amount="10.00", currency="INR",
                   payment_date=date.today(), method=Payment.Method.BANK,
                   transaction_reference="TXN-001")
    with pytest.raises(PaymentError):
        record_payment(customer=customer, amount="10.00", currency="INR",
                       payment_date=date.today(),
                       method=Payment.Method.BANK,
                       transaction_reference="TXN-001")


def test_currency_mismatch_rejected(customer):
    inv = create_invoice(customer=customer, currency="INR",
                        items=[{"description": "x", "quantity": 1,
                                "unit_price": "10.00"}])
    with pytest.raises(PaymentError):
        record_payment(customer=customer, invoice=inv,
                       amount="10.00", currency="USD",
                       payment_date=date.today(),
                       method=Payment.Method.CASH)


# ----- Refunds -----

def test_full_refund_marks_payment_refunded(customer):
    p = record_payment(customer=customer, amount="100.00", currency="INR",
                        payment_date=date.today(),
                        method=Payment.Method.CASH)
    record_refund(payment=p, amount="100.00",
                  refunded_at=datetime.now(tz=dt_tz.utc))
    p.refresh_from_db()
    assert p.status == Payment.Status.REFUNDED


def test_partial_refund_marks_payment_partially_refunded(customer):
    p = record_payment(customer=customer, amount="100.00", currency="INR",
                        payment_date=date.today(),
                        method=Payment.Method.CASH)
    record_refund(payment=p, amount="30.00",
                  refunded_at=datetime.now(tz=dt_tz.utc))
    p.refresh_from_db()
    assert p.status == Payment.Status.PARTIALLY_REFUNDED


def test_over_refund_rejected(customer):
    p = record_payment(customer=customer, amount="100.00", currency="INR",
                        payment_date=date.today(),
                        method=Payment.Method.CASH)
    with pytest.raises(PaymentError):
        record_refund(payment=p, amount="150.00",
                       refunded_at=datetime.now(tz=dt_tz.utc))


# ----- Void -----

def test_void_paid_invoice_rejected(customer):
    inv = create_invoice(customer=customer,
                        items=[{"description": "x", "quantity": 1,
                                "unit_price": "10.00"}])
    issue_invoice(invoice=inv)
    record_payment(customer=customer, invoice=inv, amount="10.00",
                    currency=inv.currency, payment_date=date.today(),
                    method=Payment.Method.CASH)
    with pytest.raises(ValueError):
        void_invoice(invoice=inv)


# ----- Webhook idempotency (Part 17 #4) -----

def test_duplicate_webhook_not_reprocessed(customer):
    calls = []
    def handler(event):
        calls.append(event.id)
        return "ok"

    new1, ev1, _ = ingest_webhook_event(
        provider="razorpay", provider_event_id="EVT-1",
        event_type="payment.captured",
        payload={"amount": 100},
        handler=handler,
    )
    new2, ev2, result2 = ingest_webhook_event(
        provider="razorpay", provider_event_id="EVT-1",
        event_type="payment.captured",
        payload={"amount": 100},
        handler=handler,
    )
    assert new1 is True
    assert new2 is False
    assert ev1.id == ev2.id
    assert len(calls) == 1
    assert WebhookEvent.objects.filter(provider="razorpay").count() == 1


def test_failed_webhook_marked_failed_and_not_retried_silently():
    def handler(event):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        ingest_webhook_event(
            provider="razorpay", provider_event_id="EVT-F",
            event_type="x", payload={},
            handler=handler,
        )
    ev = WebhookEvent.objects.get(provider="razorpay",
                                   provider_event_id="EVT-F")
    assert ev.status == WebhookEvent.Status.FAILED
    assert "boom" in ev.error


# ----- API reconciliation with analytics service -----

def test_dashboard_finance_fields_reconcile(api, owner_login, customer):
    from apps.analytics.services import today_payload
    record_payment(customer=customer, amount="500.00", currency="INR",
                   payment_date=date.today(),
                   method=Payment.Method.CASH)
    service = today_payload()
    resp = api.get("/api/v1/analytics/dashboard/today/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["gross_collections"] == service["gross_collections"]
    assert body["net_collections"] == service["net_collections"]
    assert Decimal(body["gross_collections"]) == Decimal("500.00")


# ----- Permissions -----

def test_support_cannot_create_invoice(api, make_user, customer):
    user, pwd = make_user(email="s@example.com", role_name="Customer Support")
    api.post("/api/v1/auth/login/",
             {"email": user.email, "password": pwd}, format="json")
    resp = api.post(
        "/api/v1/finance/invoices/",
        {"customer": str(customer.pk),
         "items": [{"description": "x", "quantity": "1",
                    "unit_price": "10.00"}]},
        format="json",
    )
    assert resp.status_code == 403
