import uuid

import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import apps.accounts.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=100, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("permissions", models.ManyToManyField(
                    blank=True, related_name="roles", to="accounts.permission")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("password", models.CharField(max_length=128,
                                              verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True,
                                                    verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False,
                    help_text="Designates that this user has all permissions "
                              "without explicitly assigning them.",
                    verbose_name="superuser status")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(blank=True, max_length=150)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_login_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("groups", models.ManyToManyField(
                    blank=True, related_name="user_set", related_query_name="user",
                    to="auth.group",
                    help_text="The groups this user belongs to.",
                    verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(
                    blank=True, related_name="user_set", related_query_name="user",
                    to="auth.permission",
                    help_text="Specific permissions for this user.",
                    verbose_name="user permissions")),
                ("role", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="users", to="accounts.role")),
            ],
            options={"ordering": ["email"]},
            managers=[
                ("objects", apps.accounts.managers.UserManager()),
            ],
        ),
    ]
