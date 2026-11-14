"""
Webhook idempotency (Part 17 #4).

Usage:
    ok, event, result = ingest_webhook_event(
        provider="razorpay",
        provider_event_id=event_id,
        event_type=type_,
        payload=payload,
        handler=lambda: ...
    )

Guarantees:
- A duplicate (provider, provider_event_id) is NOT reprocessed; the
  original `WebhookEvent` row is returned.
- The handler runs inside a transaction. Failures mark the event FAILED
  with the error text (no partial writes thanks to the atomic block).
- Signature verification is the caller's job — do it before calling.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Callable

from django.db import IntegrityError, transaction
from django.utils import timezone

from ..models import WebhookEvent

log = logging.getLogger(__name__)


def payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_signature(*, secret: str, payload_body: bytes,
                     provided: str) -> bool:
    """Generic HMAC-SHA256 verification, constant-time comparison."""
    mac = hmac.new(secret.encode("utf-8"), payload_body,
                   hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, provided or "")


def ingest_webhook_event(*, provider: str, provider_event_id: str,
                         event_type: str, payload: dict,
                         handler: Callable[[WebhookEvent], Any]
                         ) -> tuple[bool, WebhookEvent, Any]:
    """
    Store-or-skip the event, then call handler on first sight.
    Returns (was_new, event, handler_result_or_None).
    """
    try:
        with transaction.atomic():
            event = WebhookEvent.objects.create(
                provider=provider,
                provider_event_id=provider_event_id,
                event_type=event_type,
                payload=payload,
                payload_hash=payload_hash(payload),
            )
    except IntegrityError:
        # Already seen — fetch and return unchanged.
        event = WebhookEvent.objects.get(
            provider=provider, provider_event_id=provider_event_id)
        return False, event, None

    try:
        with transaction.atomic():
            result = handler(event)
        event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "processed_at"])
        return True, event, result
    except Exception as exc:
        log.exception("webhook handler failed")
        event.status = WebhookEvent.Status.FAILED
        event.error = str(exc)[:4000]
        event.save(update_fields=["status", "error"])
        raise
