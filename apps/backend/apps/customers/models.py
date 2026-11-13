from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        LOST = "lost", "Lost"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    phone_normalised = models.CharField(max_length=32, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    email_normalised = models.CharField(max_length=254, blank=True, db_index=True)
    address = models.CharField(max_length=500, blank=True)

    source = models.ForeignKey(
        "marketing.LeadSource",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="customers",
    )
    assigned_to = models.ForeignKey(
        "employees.Employee",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_customers",
    )

    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.ACTIVE)
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_customers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assigned_to"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.full_name


class CustomerTimelineEvent(models.Model):
    """
    Explicit, append-only timeline. Each lead conversion, activity, invoice,
    etc. writes a row here so the detail view renders a single chronological
    feed regardless of the originating table.
    """

    class Kind(models.TextChoices):
        LEAD_CONVERTED = "lead_converted", "Lead converted"
        NOTE = "note", "Note"
        STATUS_CHANGED = "status_changed", "Status changed"
        ASSIGNED = "assigned", "Assigned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                 related_name="timeline")
    kind = models.CharField(max_length=32, choices=Kind.choices)
    summary = models.CharField(max_length=255)
    data = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
