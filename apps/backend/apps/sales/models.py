from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SalesActivity(models.Model):
    class Kind(models.TextChoices):
        CALL_OUT = "call_out", "Outgoing call"
        CALL_IN = "call_in", "Incoming call"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"
        MEETING = "meeting", "Meeting"
        FOLLOW_UP = "follow_up", "Follow-up"
        WEBINAR_INVITE = "webinar_invite", "Webinar invitation"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        "leads.Lead", null=True, blank=True, on_delete=models.CASCADE,
        related_name="activities",
    )
    customer = models.ForeignKey(
        "customers.Customer", null=True, blank=True, on_delete=models.CASCADE,
        related_name="activities",
    )
    performed_by = models.ForeignKey(
        "employees.Employee", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="sales_activities",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices, db_index=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    outcome = models.CharField(max_length=120, blank=True)
    discussion_summary = models.TextField(blank=True)
    next_action = models.CharField(max_length=255, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    integration_ref = models.CharField(max_length=120, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["lead", "-occurred_at"]),
            models.Index(fields=["customer", "-occurred_at"]),
            models.Index(fields=["performed_by", "-occurred_at"]),
        ]


class FollowUp(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        "leads.Lead", null=True, blank=True, on_delete=models.CASCADE,
        related_name="followups",
    )
    customer = models.ForeignKey(
        "customers.Customer", null=True, blank=True, on_delete=models.CASCADE,
        related_name="followups",
    )
    owner = models.ForeignKey(
        "employees.Employee", on_delete=models.PROTECT,
        related_name="followups",
    )
    due_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.OPEN, db_index=True)
    summary = models.CharField(max_length=255)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_followups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_at"]
        indexes = [
            models.Index(fields=["owner", "status", "due_at"]),
        ]

    @property
    def is_overdue(self) -> bool:
        return (self.status == self.Status.OPEN
                and self.due_at < timezone.now())
