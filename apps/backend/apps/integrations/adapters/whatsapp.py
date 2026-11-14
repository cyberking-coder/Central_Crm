"""
WhatsApp Business adapter — stub.

A real implementation hits the Cloud API:
  POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
with an Authorization: Bearer token. The adapter below documents what we
need from the environment and exposes the same `send_text` signature a
future implementation will use; today it logs the attempted send instead
of making a network call.

Reads:
  WHATSAPP_PHONE_NUMBER_ID
  WHATSAPP_ACCESS_TOKEN
"""
from __future__ import annotations

import logging

from .base import env

log = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(env("WHATSAPP_PHONE_NUMBER_ID")) and bool(
        env("WHATSAPP_ACCESS_TOKEN"))


def send_text(*, to_phone: str, text: str) -> dict:
    if not is_configured():
        log.info("whatsapp.unconfigured", extra={"to": to_phone,
                                                   "text": text[:120]})
        return {"sent": False, "reason": "not_configured"}
    # Intentionally not sending yet — needs real credentials + template
    # approvals. A log entry keeps the attempt visible.
    log.info("whatsapp.pending_send", extra={"to": to_phone, "text": text[:120]})
    return {"sent": False, "reason": "adapter_disabled"}
