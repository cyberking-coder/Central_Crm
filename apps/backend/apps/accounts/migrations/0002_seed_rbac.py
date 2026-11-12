"""Seed default Permissions and Roles."""
from __future__ import annotations

from django.db import migrations


PERMISSIONS: list[tuple[str, str]] = [
    # Leads
    ("leads.read", "View leads"),
    ("leads.create", "Create leads"),
    ("leads.update", "Update leads"),
    ("leads.delete", "Delete leads"),
    ("leads.assign", "Assign leads"),
    ("leads.export", "Export leads"),
    ("leads.import", "Import leads"),
    # Customers
    ("customers.read", "View customers"),
    ("customers.create", "Create customers"),
    ("customers.update", "Update customers"),
    ("customers.delete", "Delete customers"),
    ("customers.export", "Export customers"),
    # Sales activities
    ("sales.activity.read", "View sales activities"),
    ("sales.activity.create", "Create sales activities"),
    ("sales.activity.update", "Update sales activities"),
    # Tasks
    ("tasks.read", "View tasks"),
    ("tasks.create", "Create tasks"),
    ("tasks.update", "Update tasks"),
    ("tasks.delete", "Delete tasks"),
    # Webinars
    ("webinars.read", "View webinars"),
    ("webinars.manage", "Create & edit webinars"),
    ("webinars.attendance", "Manage webinar attendance"),
    # Finance
    ("finance.read", "View finance data"),
    ("finance.manage", "Create & edit finance records"),
    ("finance.export", "Export finance data"),
    # Marketing
    ("marketing.read", "View marketing data"),
    ("marketing.manage", "Manage campaigns & sources"),
    # Employees / Departments / Users
    ("employees.read", "View employees"),
    ("employees.manage", "Create & edit employees"),
    ("departments.read", "View departments"),
    ("departments.manage", "Create & edit departments"),
    ("users.manage", "Manage users & roles"),
    # Reports & audit
    ("reports.read", "View reports"),
    ("audit.read", "View audit log"),
]

ROLES: dict[str, list[str]] = {
    "Company Owner": [p for p, _ in PERMISSIONS],
    "Company Admin": [p for p, _ in PERMISSIONS if not p.startswith("audit.")],
    "Department Manager": [
        "leads.read", "customers.read", "sales.activity.read",
        "tasks.read", "tasks.create", "tasks.update",
        "employees.read", "departments.read", "reports.read",
    ],
    "Sales Manager": [
        "leads.read", "leads.create", "leads.update", "leads.assign",
        "leads.export", "customers.read", "customers.update",
        "sales.activity.read", "tasks.read", "tasks.create", "tasks.update",
        "reports.read", "employees.read",
    ],
    "Salesperson": [
        "leads.read", "leads.update", "customers.read", "customers.update",
        "sales.activity.read", "sales.activity.create", "sales.activity.update",
        "tasks.read", "tasks.update",
    ],
    "Finance": [
        "customers.read", "finance.read", "finance.manage", "finance.export",
        "reports.read",
    ],
    "Webinar Manager": [
        "customers.read", "leads.read",
        "webinars.read", "webinars.manage", "webinars.attendance",
        "reports.read",
    ],
    "Customer Support": [
        "customers.read", "customers.update",
        "tasks.read", "tasks.update",
    ],
}


def seed(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    code_to_obj = {}
    for code, description in PERMISSIONS:
        obj, _ = Permission.objects.get_or_create(
            code=code, defaults={"description": description})
        code_to_obj[code] = obj

    for name, codes in ROLES.items():
        role, _ = Role.objects.get_or_create(name=name)
        role.permissions.set([code_to_obj[c] for c in codes])


def unseed(apps, schema_editor):
    apps.get_model("accounts", "Role").objects.all().delete()
    apps.get_model("accounts", "Permission").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
