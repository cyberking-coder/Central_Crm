"""
Email outbound adapter.

Reads standard SMTP env vars Django already knows about:
  EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
  EMAIL_USE_TLS, DEFAULT_FROM_EMAIL

When no SMTP host is configured the adapter falls back to the console
backend: nothing silently drops. Call `send_html_email` from services.
"""
from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .base import env


def is_configured() -> bool:
    return bool(env("EMAIL_HOST"))


def send_html_email(*, to: str, subject: str, text_body: str,
                    html_body: str = "") -> None:
    sender = (getattr(settings, "DEFAULT_FROM_EMAIL", None)
              or env("DEFAULT_FROM_EMAIL", "noreply@localhost"))
    msg = EmailMultiAlternatives(subject, text_body, sender, [to])
    if html_body:
        msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
