from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class RelatedKind(models.TextChoices):
        NONE = "none", "None"
        LEAD = "lead", "Lead"
        CUSTOMER = "customer", "Customer"
        WEBINAR = "webinar", "Webinar"
        DEPARTMENT = "department", "Department"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assignee = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT,
        related_name="assigned_tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_tasks",
    )

    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    priority = models.CharField(max_length=8, choices=Priority.choices,
                                default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.PENDING, db_index=True)

    related_kind = models.CharField(max_length=16, choices=RelatedKind.choices,
                                    default=RelatedKind.NONE)
    related_id = models.UUIDField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["status", "due_at"]),
        ]

    @property
    def is_overdue(self) -> bool:
        if self.status not in (self.Status.PENDING, self.Status.IN_PROGRESS):
            return False
        return bool(self.due_at and self.due_at < timezone.now())
