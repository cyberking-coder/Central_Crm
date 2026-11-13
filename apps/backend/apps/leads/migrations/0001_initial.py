import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("marketing", "0001_initial"),
        ("customers", "0001_initial"),
        ("employees", "0002_employee_department"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("full_name", models.CharField(max_length=150)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("phone_normalised", models.CharField(blank=True, db_index=True,
                                                      max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("email_normalised", models.CharField(blank=True, db_index=True,
                                                      max_length=254)),
                ("interested_product", models.CharField(blank=True, max_length=200)),
                ("status", models.CharField(
                    choices=[("new", "New"), ("unassigned", "Unassigned"),
                             ("assigned", "Assigned"), ("contacted", "Contacted"),
                             ("interested", "Interested"),
                             ("follow_up", "Follow-up required"),
                             ("webinar_invited", "Webinar invited"),
                             ("webinar_registered", "Webinar registered"),
                             ("qualified", "Qualified"),
                             ("converted", "Converted"),
                             ("lost", "Lost"), ("invalid", "Invalid")],
                    db_index=True, default="new", max_length=24)),
                ("priority", models.CharField(
                    choices=[("low", "Low"), ("medium", "Medium"),
                             ("high", "High")],
                    default="medium", max_length=8)),
                ("last_contacted_at", models.DateTimeField(blank=True, null=True)),
                ("next_followup_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("converted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="leads", to="marketing.leadsource")),
                ("campaign", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="leads", to="marketing.campaign")),
                ("assigned_to", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="assigned_leads",
                    to="employees.employee")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_leads",
                    to=settings.AUTH_USER_MODEL)),
                ("converted_customer", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="source_leads",
                    to="customers.customer")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(fields=["status", "-created_at"],
                               name="lead_status_time_idx"),
        ),
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(fields=["assigned_to", "status"],
                               name="lead_assigned_status_idx"),
        ),
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(fields=["source"], name="lead_source_idx"),
        ),
        migrations.CreateModel(
            name="LeadAssignmentHistory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("assigned_at", models.DateTimeField(auto_now_add=True,
                                                      db_index=True)),
                ("assigned_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("from_employee", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="employees.employee")),
                ("to_employee", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to="employees.employee")),
                ("lead", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="assignment_history", to="leads.lead")),
            ],
            options={"ordering": ["-assigned_at"]},
        ),
        migrations.CreateModel(
            name="LeadStatusHistory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("from_status", models.CharField(blank=True, max_length=24)),
                ("to_status", models.CharField(max_length=24)),
                ("changed_at", models.DateTimeField(auto_now_add=True,
                                                     db_index=True)),
                ("changed_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("lead", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="status_history", to="leads.lead")),
            ],
            options={"ordering": ["-changed_at"]},
        ),
    ]
