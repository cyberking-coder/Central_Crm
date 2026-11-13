from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.notifications.models import Notification
from apps.notifications.services import notify

from ..models import Task


@transaction.atomic
def complete_task(*, task: Task, actor, request=None) -> Task:
    if task.status == Task.Status.COMPLETED:
        return task
    task.status = Task.Status.COMPLETED
    task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at", "updated_at"])
    record_audit(actor=actor, action="task.completed",
                 entity_type="Task", entity_id=str(task.pk),
                 request=request)
    return task


def notify_task_assigned(task: Task) -> None:
    user = getattr(task.assignee, "user", None)
    if user is None:
        return
    notify(
        recipient=user, kind=Notification.Kind.TASK_ASSIGNED,
        title=f"New task: {task.title}",
        body=f"Due {task.due_at.isoformat() if task.due_at else 'anytime'}.",
        related_kind="task", related_id=task.pk,
    )


def sweep_overdue_tasks() -> int:
    """Emit one task_overdue notification per overdue open task (dedup)."""
    now = timezone.now()
    overdue = Task.objects.filter(
        status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
        due_at__lt=now,
    ).select_related("assignee__user")

    count = 0
    for t in overdue:
        user = getattr(t.assignee, "user", None)
        if user is None:
            continue
        exists = Notification.objects.filter(
            recipient=user, kind=Notification.Kind.TASK_OVERDUE,
            related_id=str(t.pk), is_read=False,
        ).exists()
        if exists:
            continue
        notify(
            recipient=user, kind=Notification.Kind.TASK_OVERDUE,
            title=f"Task overdue: {t.title}",
            related_kind="task", related_id=t.pk,
        )
        count += 1
    return count
