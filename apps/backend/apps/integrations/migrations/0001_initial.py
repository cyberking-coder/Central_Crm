import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WebhookSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("name", models.CharField(
                    help_text="e.g. 'n8n: notify-sales'", max_length=80)),
                ("url", models.URLField(max_length=500)),
                ("events", models.JSONField(
                    default=list,
                    help_text="List of event codes to subscribe to.")),
                ("secret", models.CharField(editable=False, max_length=80)),
                ("is_active", models.BooleanField(default=True)),
                ("failure_count", models.PositiveIntegerField(default=0)),
                ("last_delivery_at", models.DateTimeField(blank=True, null=True)),
                ("last_delivery_status", models.CharField(
                    blank=True, max_length=24)),
                ("last_error", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
