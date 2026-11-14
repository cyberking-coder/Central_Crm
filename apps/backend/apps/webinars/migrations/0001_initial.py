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
        ("marketing", "0002_seed_lead_sources"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Webinar",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("start_at", models.DateTimeField(db_index=True)),
                ("end_at", models.DateTimeField()),
                ("platform", models.CharField(blank=True, max_length=80)),
                ("registration_url", models.URLField(blank=True)),
                ("registration_limit", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(
                    choices=[("scheduled", "Scheduled"), ("live", "Live"),
                             ("completed", "Completed"),
                             ("cancelled", "Cancelled")],
                    default="scheduled", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_webinars",
                    to=settings.AUTH_USER_MODEL)),
                ("host", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="hosted_webinars",
                    to="employees.employee")),
                ("manager", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="managed_webinars",
                    to="employees.employee")),
            ],
            options={"ordering": ["-start_at"]},
        ),
        migrations.AddIndex(
            model_name="webinar",
            index=models.Index(fields=["status", "-start_at"],
                               name="webinar_status_time_idx"),
        ),
        migrations.CreateModel(
            name="WebinarRegistration",
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
                ("status", models.CharField(
                    choices=[("registered", "Registered"),
                             ("cancelled", "Cancelled")],
                    default="registered", max_length=16)),
                ("external_ref", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="webinar_registrations",
                    to="customers.customer")),
                ("lead", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="webinar_registrations", to="leads.lead")),
                ("registered_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="recorded_registrations",
                    to=settings.AUTH_USER_MODEL)),
                ("registration_source", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="webinar_registrations",
                    to="marketing.leadsource")),
                ("webinar", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="registrations", to="webinars.webinar")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="webinarregistration",
            constraint=models.UniqueConstraint(
                condition=models.Q(("email_normalised", ""), _negated=True),
                fields=("webinar", "email_normalised"),
                name="wr_unique_webinar_email",
            ),
        ),
        migrations.AddConstraint(
            model_name="webinarregistration",
            constraint=models.UniqueConstraint(
                condition=models.Q(("phone_normalised", ""), _negated=True),
                fields=("webinar", "phone_normalised"),
                name="wr_unique_webinar_phone",
            ),
        ),
        migrations.CreateModel(
            name="WebinarAttendance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("status", models.CharField(
                    choices=[("registered", "Registered (no data yet)"),
                             ("attended", "Attended"),
                             ("partial", "Partially attended"),
                             ("absent", "Absent"),
                             ("cancelled", "Cancelled")],
                    db_index=True, default="registered", max_length=16)),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("duration_minutes", models.PositiveIntegerField(
                    blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recorded_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("registration", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="attendance",
                    to="webinars.webinarregistration")),
            ],
        ),
    ]
