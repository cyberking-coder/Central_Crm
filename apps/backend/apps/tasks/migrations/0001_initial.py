import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("employees", "0002_employee_department"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False,
                                        primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("due_at", models.DateTimeField(blank=True, db_index=True,
                                                 null=True)),
                ("priority", models.CharField(
                    choices=[("low", "Low"), ("medium", "Medium"),
                             ("high", "High")],
                    default="medium", max_length=8)),
                ("status", models.CharField(
                    choices=[("pending", "Pending"),
                             ("in_progress", "In progress"),
                             ("completed", "Completed"),
                             ("cancelled", "Cancelled")],
                    db_index=True, default="pending", max_length=16)),
                ("related_kind", models.CharField(
                    choices=[("none", "None"), ("lead", "Lead"),
                             ("customer", "Customer"),
                             ("webinar", "Webinar"),
                             ("department", "Department")],
                    default="none", max_length=16)),
                ("related_id", models.UUIDField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignee", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="assigned_tasks", to="employees.employee")),
                ("created_by", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="created_tasks",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["assignee", "status"],
                               name="task_assignee_status_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["status", "due_at"],
                               name="task_status_due_idx"),
        ),
    ]
