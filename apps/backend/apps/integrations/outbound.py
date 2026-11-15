"""
Outbound webhook subscriptions.

When something interesting happens (lead.created, lead.converted,
customer.created, invoice.paid, payment.successful, task.assigned...),
we POST a signed JSON payload to every WebhookSubscription whose
`events` array includes that event name.

Delivery is retried via Celery with exponential backoff; the subscription
tracks consecutive failures and disables itself after too many.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

log = logging.getLogger(__name__)


EVENT_CHOICES = [
    ("lead.created", "Lead created"),
    ("lead.assigned", "Lead assigned"),
    ("lead.converted", "Lead converted to customer"),
    ("customer.created", "Customer created"),
    ("invoice.issued", "Invoice issued"),
    ("invoice.paid", "Invoice fully paid"),
    ("payment.successful", "Payment recorded"),
    ("payment.refunded", "Payment refunded"),
    ("task.assigned", "Task assigned"),
    ("task.completed", "Task completed"),
    ("webinar.registration", "Webinar registration"),
]
ALL_EVENTS = {code for code, _ in EVENT_CHOICES}


class WebhookSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80,
                             help_text="e.g. 'n8n: notify-sales'")
    url = models.URLField(max_length=500)
    events = models.JSONField(default=list,
                              help_text="List of event codes to subscribe to.")
    secret = models.CharField(max_length=80, editable=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")
    failure_count = models.PositiveIntegerField(default=0)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_delivery_status = models.CharField(max_length=24, blank=True)
    last_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "integrations"
        ordering = ["-created_at"]

    def generate_secret(self) -> None:
        if not self.secret:
            self.secret = secrets.token_urlsafe(32)

    def matches(self, event: str) -> bool:
        return self.is_active and event in (self.events or [])


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def fire_event(event: str, payload: dict[str, Any]) -> None:
    """Enumerate subscribers and dispatch a Celery delivery per match."""
    if event not in ALL_EVENTS:
        log.warning("outbound: unknown event %s", event)
        return
    subs = WebhookSubscription.objects.filter(is_active=True)
    body = {"event": event, "data": payload,
            "at": timezone.now().isoformat()}
    raw = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    for sub in subs:
        if not sub.matches(event):
            continue
        # Lazy import to avoid celery import at Django-startup time.
        from .tasks import deliver_webhook_task
        deliver_webhook_task.delay(
            subscription_id=str(sub.id),
            url=sub.url,
            payload_bytes=raw.decode("utf-8"),
            signature=sign(sub.secret, raw),
        )
