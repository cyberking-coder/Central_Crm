import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("leads", "0001_initial"),
        ("customers", "0001_initial"),
        ("employees", "0002_employee_department"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Communication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("channel", models.CharField(
                    choices=[("whatsapp", "WhatsApp"), ("sms", "SMS"),
                             ("email", "Email"), ("call", "Phone call"),
                             ("other", "Other")],
                    max_length=16)),
                ("direction", models.CharField(
                    choices=[("in", "Inbound"), ("out", "Outbound")],
                    max_length=4)),
                ("from_address", models.CharField(
                    blank=True,
                    help_text="Phone, email, or identifier.",
                    max_length=255)),
                ("to_address", models.CharField(blank=True, max_length=255)),
                ("subject", models.CharField(
                    blank=True,
                    help_text="Email subject or call title.",
                    max_length=255)),
                ("body", models.TextField(
                    blank=True,
                    help_text="Message text / email body / call transcript.")),
                ("attachments", models.JSONField(
                    blank=True, default=list,
                    help_text="List of {name, url, mime} dicts.")),
                ("duration_seconds", models.PositiveIntegerField(
                    blank=True, null=True)),
                ("recording_url", models.URLField(blank=True, max_length=500)),
                ("external_ref", models.CharField(
                    blank=True, db_index=True,
                    help_text="Provider's own id (WABA message id, email "
                              "Message-ID, call sid). Deduplicates replays.",
                    max_length=120)),
                ("occurred_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="communications",
                    to="customers.customer")),
                ("lead", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="communications", to="leads.lead")),
                ("employee", models.ForeignKey(
                    blank=True, null=True,
                    help_text="Employee on our side, if known.",
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="communications",
                    to="employees.employee")),
                ("pushed_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-occurred_at"]},
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["lead", "-occurred_at"],
                               name="comm_lead_time_idx"),
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["customer", "-occurred_at"],
                               name="comm_cust_time_idx"),
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["channel", "-occurred_at"],
                               name="comm_channel_time_idx"),
        ),
        migrations.AddConstraint(
            model_name="communication",
            constraint=models.UniqueConstraint(
                condition=models.Q(("external_ref", ""), _negated=True),
                fields=("channel", "external_ref"),
                name="communication_channel_ref_uniq",
            ),
        ),
    ]
