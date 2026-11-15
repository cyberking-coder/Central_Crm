"""Celery tasks for outbound webhook delivery."""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)


@shared_task(
    bind=True, max_retries=5, default_retry_delay=30,
    name="apps.integrations.tasks.deliver_webhook_task",
)
def deliver_webhook_task(self, *, subscription_id: str, url: str,
                         payload_bytes: str, signature: str):
    import urllib.request
    import urllib.error

    from .outbound import WebhookSubscription

    try:
        sub = WebhookSubscription.objects.get(pk=subscription_id)
    except WebhookSubscription.DoesNotExist:
        return

    req = urllib.request.Request(
        url, data=payload_bytes.encode("utf-8"), method="POST",
        headers={
            "Content-Type": "application/json",
            "X-CCRM-Signature": signature,
            "User-Agent": "central-crm-webhook/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except Exception as exc:
        log.warning("outbound: delivery failed for %s: %s", url, exc)
        sub.failure_count += 1
        sub.last_delivery_at = timezone.now()
        sub.last_delivery_status = "error"
        sub.last_error = str(exc)[:500]
        if sub.failure_count >= 20:
            sub.is_active = False
        sub.save(update_fields=["failure_count", "last_delivery_at",
                                 "last_delivery_status", "last_error",
                                 "is_active", "updated_at"])
        raise self.retry(exc=exc)

    sub.last_delivery_at = timezone.now()
    sub.last_delivery_status = str(status)
    if 200 <= status < 300:
        sub.failure_count = 0
        sub.last_error = ""
    else:
        sub.failure_count += 1
        sub.last_error = f"HTTP {status}"
        if sub.failure_count >= 20:
            sub.is_active = False
    sub.save(update_fields=["failure_count", "last_delivery_at",
                             "last_delivery_status", "last_error",
                             "is_active", "updated_at"])
    if status >= 500:
        raise self.retry(exc=Exception(f"HTTP {status}"))
