"""
Razorpay webhook adapter.

Reads:
  RAZORPAY_WEBHOOK_SECRET

Verifies the HMAC signature from the `X-Razorpay-Signature` header,
stores the inbound event via the shared WebhookEvent idempotency store
(Part 17 #4), then dispatches to a handler that records a Payment or
Refund through `apps.finance.services`.

No fake success paths: unknown event types are stored but marked
PROCESSED with no side effect, so replays stay idempotent and audit
logs show exactly what was seen.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone as dt_tz
from decimal import Decimal

from apps.customers.models import Customer
from apps.finance.models import Payment
from apps.finance.services.payments import PaymentError, record_payment, record_refund

from .base import env

log = logging.getLogger(__name__)

PROVIDER = "razorpay"


def is_configured() -> bool:
    return bool(env("RAZORPAY_WEBHOOK_SECRET"))


def verify_signature(*, raw_body: bytes, provided: str) -> bool:
    secret = env("RAZORPAY_WEBHOOK_SECRET")
    if not secret or not provided:
        return False
    mac = hmac.new(secret.encode("utf-8"), raw_body,
                   hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, provided)


def _parse_amount_paise_to_decimal(paise: int | str) -> Decimal:
    """Razorpay amounts are in the smallest currency unit (paise)."""
    return (Decimal(str(paise)) / Decimal("100")).quantize(Decimal("0.01"))


def _find_customer_from_event(event_payload: dict) -> Customer | None:
    entity = (
        event_payload.get("payload", {})
        .get("payment", {})
        .get("entity")
        or {}
    )
    email = (entity.get("email") or "").strip().lower()
    phone = (entity.get("contact") or "").strip()
    qs = Customer.objects.none()
    if email:
        qs = Customer.objects.filter(email_normalised=email)
    if not qs.exists() and phone:
        from apps.core.normalisation import normalise_phone
        qs = Customer.objects.filter(
            phone_normalised=normalise_phone(phone))
    return qs.first()


def handle_event(event) -> dict:
    """
    Dispatch handler for a stored WebhookEvent. Called from inside the
    atomic block in `ingest_webhook_event` — raising rolls the finance
    write back while keeping the dedup key.
    """
    payload = event.payload or {}
    event_type = event.event_type
    entity = (
        payload.get("payload", {}).get("payment", {}).get("entity") or {}
    )

    if event_type == "payment.captured":
        amount = _parse_amount_paise_to_decimal(entity.get("amount", 0))
        currency = (entity.get("currency") or "INR").upper()
        pay_id = entity.get("id") or ""
        customer = _find_customer_from_event(payload)
        if customer is None:
            log.warning("razorpay: no customer match for payment %s", pay_id)
            return {"skipped": "no_customer_match", "payment_entity_id": pay_id}
        p = record_payment(
            customer=customer,
            amount=amount, currency=currency,
            payment_date=datetime.now(tz=dt_tz.utc).date(),
            method=Payment.Method.GATEWAY,
            transaction_reference=pay_id,
            status=Payment.Status.SUCCESSFUL,
            source=Payment.Source.GATEWAY,
            external_event_ref=event.provider_event_id,
        )
        return {"recorded_payment_id": str(p.pk)}

    if event_type == "payment.failed":
        amount = _parse_amount_paise_to_decimal(entity.get("amount", 0))
        currency = (entity.get("currency") or "INR").upper()
        pay_id = entity.get("id") or ""
        customer = _find_customer_from_event(payload)
        if customer is None:
            return {"skipped": "no_customer_match", "payment_entity_id": pay_id}
        try:
            p = record_payment(
                customer=customer, amount=amount, currency=currency,
                payment_date=datetime.now(tz=dt_tz.utc).date(),
                method=Payment.Method.GATEWAY,
                transaction_reference=pay_id,
                status=Payment.Status.FAILED,
                source=Payment.Source.GATEWAY,
                external_event_ref=event.provider_event_id,
            )
        except PaymentError:
            # Already recorded; nothing to do.
            return {"skipped": "duplicate"}
        return {"recorded_payment_id": str(p.pk)}

    if event_type == "refund.processed":
        refund_entity = payload.get("payload", {}).get("refund", {}).get(
            "entity") or {}
        pay_ref = refund_entity.get("payment_id") or ""
        amount = _parse_amount_paise_to_decimal(refund_entity.get("amount", 0))
        if not pay_ref:
            return {"skipped": "missing_payment_ref"}
        payment = Payment.objects.filter(
            transaction_reference=pay_ref, method=Payment.Method.GATEWAY,
        ).first()
        if payment is None:
            return {"skipped": "unknown_payment_ref",
                    "payment_ref": pay_ref}
        r = record_refund(
            payment=payment, amount=amount,
            refunded_at=datetime.now(tz=dt_tz.utc),
            external_ref=refund_entity.get("id", ""),
        )
        return {"recorded_refund_id": str(r.pk)}

    # Unknown — stored, no side effect.
    return {"ignored_type": event_type}
