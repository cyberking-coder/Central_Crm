from __future__ import annotations

import uuid

from django.db import models


class LeadSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    source = models.ForeignKey(
        LeadSource, on_delete=models.PROTECT, related_name="campaigns"
    )
    utm_source = models.CharField(max_length=80, blank=True)
    utm_medium = models.CharField(max_length=80, blank=True)
    utm_campaign = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, blank=True,
                                 help_text="ISO-3; blank = company default.")
    spend = models.DecimalField(max_digits=14, decimal_places=2, default=0,
                                 help_text="Total ad spend recorded against this campaign.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "name"],
                                    name="campaign_source_name_uniq"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.name
