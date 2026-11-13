from __future__ import annotations

from rest_framework import serializers

from .models import FollowUp, SalesActivity


class SalesActivitySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(
        source="performed_by.full_name", read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = SalesActivity
        fields = ["id", "lead", "customer", "performed_by", "performed_by_name",
                  "kind", "kind_label", "occurred_at", "outcome",
                  "discussion_summary", "next_action", "duration_minutes",
                  "integration_ref", "created_at"]
        read_only_fields = ["id", "created_at", "performed_by_name", "kind_label"]

    def validate(self, attrs):
        if not attrs.get("lead") and not attrs.get("customer"):
            raise serializers.ValidationError(
                "Activity must be linked to a lead or a customer.")
        return attrs


class FollowUpSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = FollowUp
        fields = ["id", "lead", "customer", "owner", "owner_name",
                  "due_at", "status", "summary", "is_overdue",
                  "completed_at", "created_at", "updated_at"]
        read_only_fields = ["id", "owner_name", "is_overdue", "completed_at",
                            "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("lead") and not attrs.get("customer"):
            raise serializers.ValidationError(
                "Follow-up must be linked to a lead or a customer.")
        return attrs
