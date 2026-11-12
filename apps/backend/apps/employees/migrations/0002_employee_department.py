import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0001_initial"),
        ("departments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="employees", to="departments.department"),
        ),
        migrations.AddIndex(
            model_name="employee",
            index=models.Index(fields=["department"], name="emp_dept_idx"),
        ),
    ]
