"""
Named API tokens for machine-to-machine access.

- Multiple active tokens per user, each with a human name
  (e.g. "n8n-production", "zapier-staging").
- The raw key is shown exactly once at creation; only the SHA-256 hash
  is stored, so a leaked database doesn't leak tokens.
- `last_used_at` is updated on every successful auth (throttled so we
  don't hammer the DB — one update per minute).
- Authentication bypasses CSRF (API clients don't carry a session).
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from rest_framework import authentication, exceptions


KEY_PREFIX = "ccrm_"
KEY_BYTES = 32  # 32 bytes → 43 url-safe chars


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ApiToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    name = models.CharField(max_length=80,
                             help_text="Human label, e.g. 'n8n-production'.")
    key_hash = models.CharField(max_length=64, unique=True, db_index=True,
                                 editable=False)
    prefix = models.CharField(max_length=12, editable=False,
                               help_text="First few characters, for display.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "accounts"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"],
                                    name="apitoken_user_name_uniq"),
        ]

    @classmethod
    def create_for_user(cls, user, name: str) -> tuple["ApiToken", str]:
        """Return (token_row, raw_key). The raw key is NOT stored."""
        raw = KEY_PREFIX + secrets.token_urlsafe(KEY_BYTES)
        tok = cls.objects.create(
            user=user, name=name,
            key_hash=_hash(raw),
            prefix=raw[: len(KEY_PREFIX) + 6],
        )
        return tok, raw

    def touch_used(self) -> None:
        now = timezone.now()
        if (self.last_used_at is None
                or (now - self.last_used_at) > timedelta(minutes=1)):
            self.last_used_at = now
            type(self).objects.filter(pk=self.pk).update(last_used_at=now)


class ApiTokenAuthentication(authentication.BaseAuthentication):
    """
    Bearer <token> authentication. Does not enforce CSRF — token presence
    is the protection against CSRF (browsers can't attach a custom header
    from another site without the user's cooperation).
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode(
            "iso-8859-1")
        if not header or not header.lower().startswith(self.keyword.lower() + " "):
            return None
        raw = header.split(" ", 1)[1].strip()
        if not raw:
            return None
        try:
            tok = ApiToken.objects.select_related("user").get(
                key_hash=_hash(raw), is_active=True)
        except ApiToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid or revoked token.")
        if not tok.user.is_active:
            raise exceptions.AuthenticationFailed("User is inactive.")
        tok.touch_used()
        return (tok.user, tok)

    def authenticate_header(self, request):
        return self.keyword
