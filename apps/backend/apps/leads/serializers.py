from __future__ import annotations

from rest_framework import serializers

from apps.core.normalisation import normalise_email, normalise_phone
from apps.employees.models import Employee

from .models import Lead, LeadAssignmentHistory, LeadStatusHistory


class LeadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name",
                                             read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "full_name", "phone", "email",
            "source", "source_name", "campaign", "campaign_name",
            "interested_product", "status", "priority",
            "assigned_to", "assigned_to_name",
            "last_contacted_at", "next_followup_at", "notes",
            "converted_customer", "converted_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "source_name", "campaign_name", "assigned_to_name",
            "converted_customer", "converted_at", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        # Prevent client from manually setting converted status.
        status = attrs.get("status")
        if status == Lead.Status.CONVERTED:
            raise serializers.ValidationError(
                {"status": "Use the convert endpoint instead."})
        return attrs

    def create(self, validated):
        validated["phone_normalised"] = normalise_phone(validated.get("phone"))
        validated["email_normalised"] = normalise_email(validated.get("email"))
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated["created_by"] = request.user
        return super().create(validated)

    def update(self, instance, validated):
        if "phone" in validated:
            validated["phone_normalised"] = normalise_phone(validated["phone"])
        if "email" in validated:
            validated["email_normalised"] = normalise_email(validated["email"])
        return super().update(instance, validated)


class LeadAssignSerializer(serializers.Serializer):
    employee_id = serializers.UUIDField(allow_null=True, required=False)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_employee_id(self, value):
        if value is None:
            return None
        if not Employee.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Employee not found.")
        return value


class LeadAssignmentHistorySerializer(serializers.ModelSerializer):
    from_employee_name = serializers.CharField(
        source="from_employee.full_name", read_only=True)
    to_employee_name = serializers.CharField(
        source="to_employee.full_name", read_only=True)
    assigned_by_email = serializers.CharField(
        source="assigned_by.email", read_only=True)

    class Meta:
        model = LeadAssignmentHistory
        fields = ["id", "from_employee", "from_employee_name",
                  "to_employee", "to_employee_name",
                  "assigned_by", "assigned_by_email",
                  "reason", "assigned_at"]


class LeadStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadStatusHistory
        fields = ["id", "from_status", "to_status", "changed_by", "changed_at"]
