from __future__ import annotations

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10,
                                         trim_whitespace=False)


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_role(self, obj) -> str | None:
        return obj.role.name if obj.role_id else None

    def get_permissions(self, obj) -> list[str]:
        if obj.is_superuser:
            return ["*"]
        if obj.role_id is None:
            return []
        return sorted(obj.role.permission_codes())
