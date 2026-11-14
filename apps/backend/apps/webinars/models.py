from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Webinar(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField()
    platform = models.CharField(max_length=80, blank=True)
    registration_url = models.URLField(blank=True)
    # 0 = unlimited
    registration_limit = models.PositiveIntegerField(default=0)

    host = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="hosted_webinars",
    )
    manager = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="managed_webinars",
    )

    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.SCHEDULED)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_webinars",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["status", "-start_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class WebinarRegistration(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webinar = models.ForeignKey(
        Webinar, on_delete=models.CASCADE, related_name="registrations",
    )
    lead = models.ForeignKey(
        "leads.Lead", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="webinar_registrations",
    )
    customer = models.ForeignKey(
        "customers.Customer", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="webinar_registrations",
    )

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    phone_normalised = models.CharField(max_length=32, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    email_normalised = models.CharField(max_length=254, blank=True, db_index=True)

    registration_source = models.ForeignKey(
        "marketing.LeadSource", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="webinar_registrations",
    )
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.REGISTERED)
    external_ref = models.CharField(max_length=120, blank=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="recorded_registrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Enforce unique registration per webinar when contact info present.
            # Null phone_normalised rows duplicate-check is done in the service.
            models.UniqueConstraint(
                fields=["webinar", "email_normalised"],
                condition=~models.Q(email_normalised=""),
                name="wr_unique_webinar_email",
            ),
            models.UniqueConstraint(
                fields=["webinar", "phone_normalised"],
                condition=~models.Q(phone_normalised=""),
                name="wr_unique_webinar_phone",
            ),
        ]


class WebinarAttendance(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered (no data yet)"
        ATTENDED = "attended", "Attended"
        PARTIAL = "partial", "Partially attended"
        ABSENT = "absent", "Absent"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.OneToOneField(
        WebinarRegistration, on_delete=models.CASCADE,
        related_name="attendance",
    )
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.REGISTERED, db_index=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)
