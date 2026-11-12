from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api() -> APIClient:
    return APIClient(enforce_csrf_checks=False)


@pytest.fixture
def api_csrf() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def make_user(db):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import Role

    User = get_user_model()

    def _make(email: str = "user@example.com",
              password: str = "Testpass!2345",
              role_name: str | None = None,
              is_active: bool = True,
              is_superuser: bool = False):
        role = Role.objects.get(name=role_name) if role_name else None
        user = User.objects.create_user(
            email=email, password=password,
            full_name=email.split("@")[0],
            role=role,
            is_active=is_active,
            is_superuser=is_superuser,
            is_staff=is_superuser,
        )
        return user, password
    return _make
