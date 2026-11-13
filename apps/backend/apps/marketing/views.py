from __future__ import annotations

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import HasPermissionCode

from .models import Campaign, LeadSource
from .serializers import CampaignSerializer, LeadSourceSerializer


LEAD_SOURCE_PERMS = {
    "list": "leads.read", "retrieve": "leads.read",
    "create": "marketing.manage", "update": "marketing.manage",
    "partial_update": "marketing.manage", "destroy": "marketing.manage",
}

CAMPAIGN_PERMS = {
    "list": "marketing.read", "retrieve": "marketing.read",
    "create": "marketing.manage", "update": "marketing.manage",
    "partial_update": "marketing.manage", "destroy": "marketing.manage",
}


class LeadSourceViewSet(viewsets.ModelViewSet):
    queryset = LeadSource.objects.filter(is_active=True)
    serializer_class = LeadSourceSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def get_permissions(self):
        self.required_permission = LEAD_SOURCE_PERMS.get(
            self.action, "leads.read")
        return super().get_permissions()


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.select_related("source").all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, HasPermissionCode]

    def get_permissions(self):
        self.required_permission = CAMPAIGN_PERMS.get(
            self.action, "marketing.read")
        return super().get_permissions()
