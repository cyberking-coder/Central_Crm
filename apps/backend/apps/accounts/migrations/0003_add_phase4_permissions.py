from django.db import migrations


NEW_PERMISSIONS = [
    ("sales.followup.read", "View follow-ups"),
    ("sales.followup.manage", "Create & edit follow-ups"),
    ("notifications.read", "View own notifications"),
]

ROLE_ADDITIONS = {
    "Company Owner":   [p for p, _ in NEW_PERMISSIONS],
    "Company Admin":   [p for p, _ in NEW_PERMISSIONS if not p.startswith("audit.")],
    "Department Manager": ["sales.followup.read", "notifications.read"],
    "Sales Manager":   ["sales.followup.read", "sales.followup.manage",
                        "notifications.read"],
    "Salesperson":     ["sales.followup.read", "sales.followup.manage",
                        "notifications.read"],
    "Finance":         ["notifications.read"],
    "Webinar Manager": ["sales.followup.read", "notifications.read"],
    "Customer Support":["sales.followup.read", "notifications.read"],
}


def forward(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    code_map = {}
    for code, description in NEW_PERMISSIONS:
        obj, _ = Permission.objects.get_or_create(
            code=code, defaults={"description": description})
        code_map[code] = obj

    for role_name, codes in ROLE_ADDITIONS.items():
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            continue
        for c in codes:
            role.permissions.add(code_map[c])


def backward(apps, schema_editor):
    apps.get_model("accounts", "Permission").objects.filter(
        code__in=[c for c, _ in NEW_PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_seed_rbac")]
    operations = [migrations.RunPython(forward, backward)]
