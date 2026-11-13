from __future__ import annotations

from rest_framework import serializers

from apps.core.normalisation import normalise_email, normalise_phone

from .models import Customer, CustomerTimelineEvent


class CustomerSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name",
                                             read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone", "email", "address",
                  "source", "source_name", "assigned_to", "assigned_to_name",
                  "status", "tags", "notes",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "source_name", "assigned_to_name",
                            "created_at", "updated_at"]

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


class CustomerTimelineSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = CustomerTimelineEvent
        fields = ["id", "kind", "summary", "data", "actor", "actor_email",
                  "occurred_at"]
