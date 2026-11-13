from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        UNASSIGNED = "unassigned", "Unassigned"
        ASSIGNED = "assigned", "Assigned"
        CONTACTED = "contacted", "Contacted"
        INTERESTED = "interested", "Interested"
        FOLLOW_UP = "follow_up", "Follow-up required"
        WEBINAR_INVITED = "webinar_invited", "Webinar invited"
        WEBINAR_REGISTERED = "webinar_registered", "Webinar registered"
        QUALIFIED = "qualified", "Qualified"
        CONVERTED = "converted", "Converted"
        LOST = "lost", "Lost"
        INVALID = "invalid", "Invalid"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    phone_normalised = models.CharField(max_length=32, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    email_normalised = models.CharField(max_length=254, blank=True, db_index=True)

    source = models.ForeignKey(
        "marketing.LeadSource",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="leads",
    )
    campaign = models.ForeignKey(
        "marketing.Campaign",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="leads",
    )
    interested_product = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=24, choices=Status.choices,
                              default=Status.NEW, db_index=True)
    priority = models.CharField(max_length=8, choices=Priority.choices,
                                default=Priority.MEDIUM)

    assigned_to = models.ForeignKey(
        "employees.Employee",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_leads",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_leads",
    )

    last_contacted_at = models.DateTimeField(null=True, blank=True)
    next_followup_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    converted_customer = models.ForeignKey(
        "customers.Customer",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="source_leads",
    )
    converted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.full_name} ({self.status})"


class LeadAssignmentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE,
                             related_name="assignment_history")
    from_employee = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")
    to_employee = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")
    reason = models.CharField(max_length=255, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-assigned_at"]


class LeadStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE,
                             related_name="status_history")
    from_status = models.CharField(max_length=24, blank=True)
    to_status = models.CharField(max_length=24)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+")
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-changed_at"]
