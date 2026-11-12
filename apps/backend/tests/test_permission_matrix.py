"""
Part 17 control #3 — Role × Permission matrix.

Verifies the seeded RBAC matches the matrix declared in Phase 0.
Grows as modules land.
"""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.accounts.permissions import HasPermissionCode


pytestmark = pytest.mark.django_db


EXPECTED: dict[str, set[str]] = {
    "Company Owner": {"leads.read", "leads.delete", "finance.manage",
                      "users.manage", "audit.read"},
    "Company Admin": {"leads.read", "finance.manage", "users.manage"},
    "Sales Manager": {"leads.read", "leads.assign", "leads.export"},
    "Salesperson": {"leads.read", "leads.update",
                    "sales.activity.create"},
    "Finance": {"finance.read", "finance.manage", "finance.export"},
    "Webinar Manager": {"webinars.manage", "webinars.attendance"},
    "Customer Support": {"customers.read", "customers.update",
                         "tasks.update"},
    "Department Manager": {"employees.read", "tasks.create"},
}

NEVER_GRANTED: dict[str, set[str]] = {
    "Salesperson": {"finance.manage", "users.manage", "audit.read"},
    "Customer Support": {"finance.manage", "leads.delete", "users.manage"},
    "Webinar Manager": {"finance.manage", "users.manage"},
    "Finance": {"users.manage", "leads.delete"},
    "Company Admin": {"audit.read"},  # audit view is owner-only per seed
}


@pytest.mark.parametrize("role_name,codes", list(EXPECTED.items()))
def test_role_has_required_permissions(role_name, codes):
    role = Role.objects.get(name=role_name)
    assigned = role.permission_codes()
    missing = codes - assigned
    assert not missing, f"{role_name} missing {missing}"


@pytest.mark.parametrize("role_name,codes", list(NEVER_GRANTED.items()))
def test_role_does_not_have_restricted_permissions(role_name, codes):
    role = Role.objects.get(name=role_name)
    assigned = role.permission_codes()
    leaks = codes & assigned
    assert not leaks, f"{role_name} unexpectedly has {leaks}"


# ----- HasPermissionCode behaviour -----

class _FakeView:
    required_permission = "leads.read"


def test_unauthenticated_denied(rf):
    from django.contrib.auth.models import AnonymousUser
    req = rf.get("/")
    req.user = AnonymousUser()
    assert HasPermissionCode().has_permission(req, _FakeView()) is False


def test_deactivated_denied(rf, make_user):
    user, _ = make_user(email="d@example.com",
                        role_name="Salesperson", is_active=False)
    req = rf.get("/")
    req.user = user
    assert HasPermissionCode().has_permission(req, _FakeView()) is False


def test_superuser_bypasses(rf, make_user):
    user, _ = make_user(email="su@example.com", is_superuser=True)
    req = rf.get("/")
    req.user = user
    assert HasPermissionCode().has_permission(req, _FakeView()) is True


def test_role_grants_permission(rf, make_user):
    user, _ = make_user(email="s@example.com", role_name="Salesperson")
    req = rf.get("/")
    req.user = user
    assert HasPermissionCode().has_permission(req, _FakeView()) is True


def test_role_without_code_denied(rf, make_user):
    user, _ = make_user(email="w@example.com", role_name="Webinar Manager")

    class ViewNeedingFinance:
        required_permission = "finance.manage"

    req = rf.get("/")
    req.user = user
    assert HasPermissionCode().has_permission(req, ViewNeedingFinance()) is False
