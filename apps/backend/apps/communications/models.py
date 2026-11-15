"""
Message-level communications store.

One row per actual message/email/call. Pushed in by integrations
(WhatsApp Cloud API, Gmail/IMAP, Exotel, Twilio, ...) via the
`/api/v1/communications/` endpoint, usually through an n8n workflow.

A row ALWAYS belongs to either a Lead or a Customer (or both), and is
idempotent per (channel, external_ref) so replays from n8n don't create
duplicates.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Communication(models.Model):
    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"
        CALL = "call", "Phone call"
        OTHER = "other", "Other"

    class Direction(models.TextChoices):
        INBOUND = "in", "Inbound"
        OUTBOUND = "out", "Outbound"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    lead = models.ForeignKey(
        "leads.Lead", null=True, blank=True, on_delete=models.CASCADE,
        related_name="communications",
    )
    customer = models.ForeignKey(
        "customers.Customer", null=True, blank=True, on_delete=models.CASCADE,
        related_name="communications",
    )

    channel = models.CharField(max_length=16, choices=Channel.choices)
    direction = models.CharField(max_length=4, choices=Direction.choices)

    # Who sent / received it.
    from_address = models.CharField(max_length=255, blank=True,
                                    help_text="Phone, email, or identifier.")
    to_address = models.CharField(max_length=255, blank=True)
    employee = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="communications",
        help_text="Employee on our side, if known.",
    )

    subject = models.CharField(max_length=255, blank=True,
                                help_text="Email subject or call title.")
    body = models.TextField(blank=True,
                             help_text="Message text / email body / call transcript.")
    attachments = models.JSONField(default=list, blank=True,
                                    help_text="List of {name, url, mime} dicts.")

    # Call-specific fields (ignored for non-call channels)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    recording_url = models.URLField(blank=True, max_length=500)

    external_ref = models.CharField(
        max_length=120, blank=True, db_index=True,
        help_text="Provider's own id (WABA message id, email Message-ID, "
                  "call sid). Deduplicates replays.",
    )
    occurred_at = models.DateTimeField(db_index=True)

    pushed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["lead", "-occurred_at"]),
            models.Index(fields=["customer", "-occurred_at"]),
            models.Index(fields=["channel", "-occurred_at"]),
        ]
        constraints = [
            # Prevent duplicates from replayed webhooks.
            models.UniqueConstraint(
                fields=["channel", "external_ref"],
                condition=~models.Q(external_ref=""),
                name="communication_channel_ref_uniq",
            ),
        ]
