from __future__ import annotations

from rest_framework import serializers

from .models import Communication


class CommunicationSerializer(serializers.ModelSerializer):
    channel_label = serializers.CharField(source="get_channel_display",
                                           read_only=True)
    employee_name = serializers.CharField(source="employee.full_name",
                                           read_only=True, default=None)

    class Meta:
        model = Communication
        fields = ["id", "lead", "customer",
                  "channel", "channel_label", "direction",
                  "from_address", "to_address",
                  "employee", "employee_name",
                  "subject", "body", "attachments",
                  "duration_seconds", "recording_url",
                  "external_ref", "occurred_at", "created_at"]
        read_only_fields = ["id", "channel_label", "employee_name",
                            "created_at"]


class CommunicationIngestSerializer(serializers.Serializer):
    """Input for the n8n-facing ingest endpoint."""
    channel = serializers.ChoiceField(choices=Communication.Channel.choices)
    direction = serializers.ChoiceField(choices=Communication.Direction.choices)
    occurred_at = serializers.DateTimeField()
    # Contact resolution — provide at least one.
    lead_id = serializers.UUIDField(required=False, allow_null=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    contact_email = serializers.CharField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    # Payload
    from_address = serializers.CharField(required=False, allow_blank=True,
                                          max_length=255)
    to_address = serializers.CharField(required=False, allow_blank=True,
                                        max_length=255)
    subject = serializers.CharField(required=False, allow_blank=True,
                                     max_length=255)
    body = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(
        child=serializers.DictField(), required=False, default=list,
    )
    duration_seconds = serializers.IntegerField(required=False, min_value=0,
                                                 allow_null=True)
    recording_url = serializers.URLField(required=False, allow_blank=True)
    external_ref = serializers.CharField(required=False, allow_blank=True,
                                          max_length=120)
