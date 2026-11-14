from rest_framework import serializers

from .models import Campaign, LeadSource


class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = ["id", "name", "slug", "is_active"]
        read_only_fields = ["id"]


class CampaignSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Campaign
        fields = ["id", "name", "source", "source_name",
                  "utm_source", "utm_medium", "utm_campaign",
                  "start_date", "end_date", "is_active",
                  "currency", "spend",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "source_name"]
