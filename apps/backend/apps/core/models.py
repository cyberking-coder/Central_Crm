"""Shared model mixins and bases."""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class UUIDPrimaryKeyModel(models.Model):
    """UUID primary key for business entities (Part 17: schema consistency)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """Adds created_at / updated_at — stored in UTC (Part 17 control #6)."""

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Archival mixin. Never applied to financial transactions or audit rows
    (Part 17 control #5).
    """

    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def archive(self) -> None:
        if self.archived_at is None:
            self.archived_at = timezone.now()
            self.save(update_fields=["archived_at"])


class UUIDTimestampedModel(UUIDPrimaryKeyModel, TimestampedModel):
    class Meta:
        abstract = True
