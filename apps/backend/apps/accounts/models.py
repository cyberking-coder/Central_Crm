"""
Accounts: User, Role, Permission.

Design decisions:
- UUID primary key on User, Role, Permission.
- Email is the username (case-insensitively unique).
- A User has exactly one Role (nullable for bootstrapping).
- Permission codes are simple strings "<module>.<action>" (e.g. "leads.read")
  decoupled from Django's contrib.auth permissions so RBAC stays independent
  of model-level codenames.
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover
        return self.code


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name

    def permission_codes(self) -> set[str]:
        return set(self.permissions.values_list("code", flat=True))


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, null=True, blank=True, related_name="users"
    )

    # Required by Django admin / auth framework
    is_staff = models.BooleanField(default=False)
    # Business-level activation. Deactivated users lose access immediately
    # (checked by LoginView and authentication). Distinct from superuser flag.
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:  # pragma: no cover
        return self.email

    def has_permission_code(self, code: str) -> bool:
        if self.is_superuser:
            return True
        if not self.is_active or self.role_id is None:
            return False
        return self.role.permissions.filter(code=code).exists()
