"""DRF permission helpers backed by Role → Permission codes."""
from __future__ import annotations

from rest_framework.permissions import BasePermission


class HasPermissionCode(BasePermission):
    """
    View-level permission class driven by a `required_permission` attribute
    on the view. Superusers bypass; deactivated users are rejected.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not user.is_active:
            return False
        if user.is_superuser:
            return True
        code = getattr(view, "required_permission", None)
        if code is None:
            # Views that opt into this class without declaring a code are
            # treated as "authenticated-only".
            return True
        return user.has_permission_code(code)


def role_has(user, code: str) -> bool:
    """Convenience helper for service-layer checks."""
    if not getattr(user, "is_authenticated", False):
        return False
    if not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.has_permission_code(code)
