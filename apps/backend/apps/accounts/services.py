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
    Email delivery is deferred to Phase 9 integrations. For now the reset
    link is written to the backend logs so an admin can relay it. This is
    documented in KNOWN_ISSUES.
    """
    link = f"/reset?uid={uid}&token={token}"
    logger.info("password_reset_link", extra={
        "user_id": str(user.pk),
        "email": user.email,
        "link": link,
    })
