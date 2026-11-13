from __future__ import annotations

from typing import Any

from .models import Notification


def notify(*, recipient, kind: str, title: str, body: str = "",
           related_kind: str = "", related_id: Any = None) -> Notification:
    if recipient is None or not getattr(recipient, "is_authenticated", True):
        return None  # type: ignore[return-value]
    return Notification.objects.create(
        recipient=recipient, kind=kind, title=title, body=body,
        related_kind=related_kind,
        related_id=str(related_id) if related_id else "",
    )
