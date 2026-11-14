from __future__ import annotations

from rest_framework import serializers

from .models import Webinar, WebinarAttendance, WebinarRegistration


class WebinarSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source="host.full_name", read_only=True)
    manager_name = serializers.CharField(source="manager.full_name", read_only=True)

    class Meta:
        model = Webinar
        fields = ["id", "title", "description",
                  "start_at", "end_at", "platform",
                  "registration_url", "registration_limit",
                  "host", "host_name", "manager", "manager_name",
                  "status",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "host_name", "manager_name",
                            "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_at": "end_at must be after start_at."})
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="registration_source.name",
                                        read_only=True)
    attendance_status = serializers.CharField(
        source="attendance.status", read_only=True, default=None)

    class Meta:
        model = WebinarRegistration
        fields = ["id", "webinar", "lead", "customer",
                  "full_name", "phone", "email",
                  "registration_source", "source_name",
                  "status", "external_ref", "attendance_status",
                  "created_at"]
        read_only_fields = ["id", "source_name", "attendance_status",
                            "created_at", "webinar"]


class RegistrationCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=32, required=False,
                                   allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    lead = serializers.UUIDField(required=False, allow_null=True)
    customer = serializers.UUIDField(required=False, allow_null=True)
    registration_source = serializers.UUIDField(required=False, allow_null=True)
    external_ref = serializers.CharField(required=False, allow_blank=True,
                                          max_length=120)


class AttendanceSerializer(serializers.ModelSerializer):
    registration_name = serializers.CharField(
        source="registration.full_name", read_only=True)

    class Meta:
        model = WebinarAttendance
        fields = ["id", "registration", "registration_name",
                  "status", "joined_at", "left_at", "duration_minutes",
                  "updated_at"]
        read_only_fields = ["id", "registration", "registration_name",
                            "updated_at"]


class AttendanceUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[c[0] for c in WebinarAttendance.Status.choices])
    joined_at = serializers.DateTimeField(required=False, allow_null=True)
    left_at = serializers.DateTimeField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(required=False, allow_null=True,
                                                 min_value=0)
