"""Service-layer helpers: password reset token generation + audit emission."""
from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import User

logger = logging.getLogger(__name__)


def make_reset_token(user: User) -> tuple[str, str]:
    """Return (uid_b64, token) pair for a password reset flow."""
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = default_token_generator.make_token(user)
    return uid, token


def decode_reset_token(uid_b64: str, token: str) -> User | None:
    try:
        uid = urlsafe_base64_decode(uid_b64).decode()
        user = User.objects.get(pk=uid, is_active=True)
    except (User.DoesNotExist, ValueError, TypeError):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user


def record_login(user: User, ip: str | None) -> None:
    user.last_login_ip = ip
    user.save(update_fields=["last_login_ip", "last_login"])


def emit_password_reset_delivery(user: User, uid: str, token: str,
                                 request: Any) -> None:
    """
    Sends the reset link via the configured email adapter. When SMTP is
    not configured, Django's console backend prints it — same end result
    for dev, no silent drops in production.
    """
    link = f"/reset?uid={uid}&token={token}"
    try:
        from apps.integrations.adapters.email_adapter import send_html_email
        send_html_email(
            to=user.email,
            subject="Reset your Central CRM password",
            text_body=(
                f"Hi {user.full_name or user.email},\n\n"
                f"Use this link to reset your password (valid for a limited time):\n"
                f"{link}\n\n"
                f"If you didn't request this, ignore the message.\n"
            ),
            html_body=(
                f"<p>Hi {user.full_name or user.email},</p>"
                f"<p>Use this link to reset your password "
                f"(valid for a limited time):</p>"
                f"<p><a href='{link}'>{link}</a></p>"
                f"<p>If you didn't request this, ignore the message.</p>"
            ),
        )
    except Exception as e:  # pragma: no cover
        logger.exception("password_reset_email_failed")
        logger.info("password_reset_link", extra={
            "user_id": str(user.pk), "email": user.email, "link": link,
            "error": str(e),
        })
