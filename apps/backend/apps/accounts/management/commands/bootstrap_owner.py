"""
One-shot command to create the first Company Owner.

Usage:
    python manage.py bootstrap_owner --email owner@example.com --password '...'

Idempotent: if a user with that email exists, the role is (re)assigned.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role


class Command(BaseCommand):
    help = "Create (or upgrade) the Company Owner user."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--full-name", default="")

    def handle(self, *args, **opts):
        User = get_user_model()
        try:
            role = Role.objects.get(name="Company Owner")
        except Role.DoesNotExist as e:
            raise CommandError(
                "Role 'Company Owner' not found. Run migrations first.") from e

        email = opts["email"].lower().strip()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": opts["full_name"],
                "is_active": True,
                "is_staff": True,
                "is_superuser": False,
                "role": role,
            },
        )
        if not created:
            user.role = role
            user.is_active = True
            user.is_staff = True
        user.set_password(opts["password"])
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"Company Owner {action}: {user.email}"))
