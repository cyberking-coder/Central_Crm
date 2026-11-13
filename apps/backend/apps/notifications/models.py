from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        LEAD_ASSIGNED = "lead_assigned", "Lead assigned"
        LEAD_REASSIGNED = "lead_reassigned", "Lead reassigned"
        TASK_ASSIGNED = "task_assigned", "Task assigned"
        TASK_DUE_SOON = "task_due_soon", "Task due soon"
        TASK_OVERDUE = "task_overdue", "Task overdue"
        FOLLOWUP_DUE = "followup_due", "Follow-up due"
        FOLLOWUP_OVERDUE = "followup_overdue", "Follow-up overdue"
        GENERIC = "generic", "Generic"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    related_kind = models.CharField(max_length=24, blank=True)
    related_id = models.CharField(max_length=64, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]
