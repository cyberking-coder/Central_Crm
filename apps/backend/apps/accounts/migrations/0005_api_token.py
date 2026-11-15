import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_add_integrations_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("name", models.CharField(
                    help_text="Human label, e.g. 'n8n-production'.",
                    max_length=80)),
                ("key_hash", models.CharField(db_index=True, editable=False,
                                               max_length=64, unique=True)),
                ("prefix", models.CharField(
                    editable=False,
                    help_text="First few characters, for display.",
                    max_length=12)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="api_tokens",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="apitoken",
            constraint=models.UniqueConstraint(
                fields=("user", "name"), name="apitoken_user_name_uniq"),
        ),
    ]
