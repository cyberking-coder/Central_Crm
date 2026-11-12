"""Audit emission helper."""
from __future__ import annotations

from typing import Any

from .models import AuditLog


def _client_ip(request) -> str | None:
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_audit(*, actor, action: str,
                 entity_type: str = "",
                 entity_id: str | None = None,
                 before: dict[str, Any] | None = None,
                 after: dict[str, Any] | None = None,
                 extra: dict[str, Any] | None = None,
                 request=None) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_email=getattr(actor, "email", "") or "",
        action=action,
        entity_type=entity_type or "",
        entity_id=str(entity_id) if entity_id else "",
        before=before or {},
        after=after or {},
        extra=extra or {},
        correlation_id=getattr(request, "correlation_id", "") if request else "",
        ip_address=_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:255] if request else ""),
    )
