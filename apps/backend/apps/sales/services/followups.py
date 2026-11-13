from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.notifications.services import notify

from ..models import FollowUp


@transaction.atomic
def complete_followup(*, followup: FollowUp, actor, request=None) -> FollowUp:
    if followup.status != FollowUp.Status.OPEN:
        return followup
    followup.status = FollowUp.Status.DONE
    followup.completed_at = timezone.now()
    followup.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit(actor=actor, action="followup.completed",
                 entity_type="FollowUp", entity_id=str(followup.pk),
                 request=request)
    return followup


@transaction.atomic
def cancel_followup(*, followup: FollowUp, actor, request=None) -> FollowUp:
    followup.status = FollowUp.Status.CANCELLED
    followup.save(update_fields=["status", "updated_at"])
    record_audit(actor=actor, action="followup.cancelled",
                 entity_type="FollowUp", entity_id=str(followup.pk),
                 request=request)
    return followup


def sweep_overdue_followups() -> int:
    """
    Mark open follow-ups whose due_at has passed as overdue in notifications.
    Called periodically (Celery Beat or management command).
    Returns the number of notifications emitted.
    """
    now = timezone.now()
    overdue = FollowUp.objects.filter(
        status=FollowUp.Status.OPEN, due_at__lt=now,
    ).select_related("owner__user")

    count = 0
    for fu in overdue:
        user = getattr(fu.owner, "user", None)
        if user is None:
            continue
        # Dedupe: only emit once per follow-up by looking for an existing
        # unread overdue notification.
        from apps.notifications.models import Notification
        exists = Notification.objects.filter(
            recipient=user,
            kind=Notification.Kind.FOLLOWUP_OVERDUE,
            related_id=str(fu.pk),
            is_read=False,
        ).exists()
        if exists:
            continue
        notify(
            recipient=user,
            kind=Notification.Kind.FOLLOWUP_OVERDUE,
            title=f"Follow-up overdue: {fu.summary}",
            body=f"Was due {fu.due_at.isoformat()}.",
            related_kind="followup", related_id=fu.pk,
        )
        count += 1
    return count
