import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("employee_code", models.CharField(max_length=32, unique=True)),
                ("full_name", models.CharField(max_length=150)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("designation", models.CharField(blank=True, max_length=100)),
                ("joining_date", models.DateField(blank=True, null=True)),
                ("employment_status", models.CharField(
                    choices=[
                        ("active", "Active"),
                        ("on_leave", "On leave"),
                        ("suspended", "Suspended"),
                        ("terminated", "Terminated"),
                    ],
                    default="active", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reporting_manager", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="direct_reports", to="employees.employee")),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="employee", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["employment_status"],
                               name="emp_status_idx"),
        ),
    ]
