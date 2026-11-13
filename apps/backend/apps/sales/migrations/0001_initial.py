import uuid

import django.db.models.deletion
import django.utils.timezone
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
            name="SalesActivity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("kind", models.CharField(
                    choices=[("call_out", "Outgoing call"),
                             ("call_in", "Incoming call"),
                             ("whatsapp", "WhatsApp"), ("email", "Email"),
                             ("meeting", "Meeting"),
                             ("follow_up", "Follow-up"),
                             ("webinar_invite", "Webinar invitation"),
                             ("other", "Other")],
                    db_index=True, max_length=24)),
                ("occurred_at", models.DateTimeField(
                    db_index=True, default=django.utils.timezone.now)),
                ("outcome", models.CharField(blank=True, max_length=120)),
                ("discussion_summary", models.TextField(blank=True)),
                ("next_action", models.CharField(blank=True, max_length=255)),
                ("duration_minutes", models.PositiveIntegerField(
                    blank=True, null=True)),
                ("integration_ref", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_activities",
                    to=settings.AUTH_USER_MODEL)),
                ("customer", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="activities", to="customers.customer")),
                ("lead", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="activities", to="leads.lead")),
                ("performed_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sales_activities",
                    to="employees.employee")),
            ],
            options={"ordering": ["-occurred_at"]},
        ),
        migrations.AddIndex(
            model_name="salesactivity",
            index=models.Index(fields=["lead", "-occurred_at"],
                               name="sa_lead_time_idx"),
        ),
        migrations.AddIndex(
            model_name="salesactivity",
            index=models.Index(fields=["customer", "-occurred_at"],
                               name="sa_customer_time_idx"),
        ),
        migrations.AddIndex(
            model_name="salesactivity",
            index=models.Index(fields=["performed_by", "-occurred_at"],
                               name="sa_perf_time_idx"),
        ),
        migrations.CreateModel(
            name="FollowUp",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("due_at", models.DateTimeField(db_index=True)),
                ("status", models.CharField(
                    choices=[("open", "Open"), ("done", "Done"),
                             ("cancelled", "Cancelled")],
                    db_index=True, default="open", max_length=16)),
                ("summary", models.CharField(max_length=255)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_followups",
                    to=settings.AUTH_USER_MODEL)),
                ("customer", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="followups", to="customers.customer")),
                ("lead", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="followups", to="leads.lead")),
                ("owner", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="followups", to="employees.employee")),
            ],
            options={"ordering": ["due_at"]},
        ),
        migrations.AddIndex(
            model_name="followup",
            index=models.Index(fields=["owner", "status", "due_at"],
                               name="fu_owner_status_due_idx"),
        ),
    ]
