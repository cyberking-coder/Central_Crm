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
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("kind", models.CharField(
                    choices=[("lead_assigned", "Lead assigned"),
                             ("lead_reassigned", "Lead reassigned"),
                             ("task_assigned", "Task assigned"),
                             ("task_due_soon", "Task due soon"),
                             ("task_overdue", "Task overdue"),
                             ("followup_due", "Follow-up due"),
                             ("followup_overdue", "Follow-up overdue"),
                             ("generic", "Generic")],
                    max_length=32)),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField(blank=True)),
                ("related_kind", models.CharField(blank=True, max_length=24)),
                ("related_id", models.CharField(blank=True, max_length=64)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True,
                                                     db_index=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("recipient", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="notif_recipient_unread_idx"),
        ),
    ]
