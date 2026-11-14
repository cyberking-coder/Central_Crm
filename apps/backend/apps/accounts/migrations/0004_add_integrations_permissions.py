from django.db import migrations


NEW = [
    ("integrations.read", "View integration status"),
    ("integrations.manage", "Manage integration settings"),
]

ROLE_ADD = {
    "Company Owner":   [p for p, _ in NEW],
    "Company Admin":   [p for p, _ in NEW],
    "Finance":         ["integrations.read"],
}


def forward(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    codes = {}
    for code, desc in NEW:
        obj, _ = Permission.objects.get_or_create(
            code=code, defaults={"description": desc})
        codes[code] = obj
    for name, want in ROLE_ADD.items():
        try:
            role = Role.objects.get(name=name)
        except Role.DoesNotExist:
            continue
        for c in want:
            role.permissions.add(codes[c])


def backward(apps, schema_editor):
    apps.get_model("accounts", "Permission").objects.filter(
        code__in=[c for c, _ in NEW]).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_add_phase4_permissions")]
    operations = [migrations.RunPython(forward, backward)]
