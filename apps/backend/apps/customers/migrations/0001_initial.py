import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("marketing", "0001_initial"),
        ("employees", "0002_employee_department"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
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
                ("address", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(
                    choices=[("active", "Active"), ("inactive", "Inactive"),
                             ("lost", "Lost")],
                    default="active", max_length=16)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="customers", to="marketing.leadsource")),
                ("assigned_to", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="assigned_customers",
                    to="employees.employee")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_customers",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["status"], name="cust_status_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["assigned_to"], name="cust_assigned_idx"),
        ),
        migrations.CreateModel(
            name="CustomerTimelineEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("kind", models.CharField(
                    choices=[("lead_converted", "Lead converted"),
                             ("note", "Note"),
                             ("status_changed", "Status changed"),
                             ("assigned", "Assigned")],
                    max_length=32)),
                ("summary", models.CharField(max_length=255)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(auto_now_add=True,
                                                     db_index=True)),
                ("actor", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="timeline", to="customers.customer")),
            ],
            options={"ordering": ["-occurred_at"]},
        ),
    ]
