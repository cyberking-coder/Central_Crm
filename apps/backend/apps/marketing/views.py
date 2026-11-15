from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasPermissionCode

from .models import Campaign, CampaignDailyMetrics, LeadSource
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


class AdMetricsIngestView(APIView):
    """
    Upsert daily ad metrics from n8n (Meta/Google Ads scheduled polls).
    Accepts:
        { "rows": [
            { "campaign_id": "...", "date": "YYYY-MM-DD",
              "spend": "123.45", "impressions": 1000, "clicks": 50,
              "conversions": 3, "currency": "INR", "source": "meta_ads" },
            ...
        ]}
    OR lookup by (utm_source, utm_medium, utm_campaign) if no campaign_id.
    """
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "marketing.manage"

    def post(self, request):
        rows = request.data.get("rows")
        if not isinstance(rows, list):
            return Response({"detail": "rows must be a list"}, status=400)

        created = 0
        updated = 0
        failed = []
        for i, row in enumerate(rows):
            campaign = None
            if row.get("campaign_id"):
                campaign = Campaign.objects.filter(pk=row["campaign_id"]).first()
            if campaign is None and row.get("utm_campaign"):
                campaign = Campaign.objects.filter(
                    utm_campaign__iexact=row["utm_campaign"],
                ).first()
            if campaign is None:
                failed.append({"row": i, "error": "campaign not found"})
                continue

            defaults = {
                "spend": Decimal(str(row.get("spend", 0))),
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "conversions": int(row.get("conversions", 0)),
                "currency": row.get("currency", "") or (campaign.currency or ""),
                "source": row.get("source", ""),
            }
            obj, was_created = CampaignDailyMetrics.objects.update_or_create(
                campaign=campaign, date=row["date"], defaults=defaults,
            )
            created += int(was_created)
            updated += int(not was_created)

        return Response({"created": created, "updated": updated, "failed": failed},
                        status=status.HTTP_200_OK)


class AdDashboardView(APIView):
    """Rollup for the Ads page. Last N days (default 30)."""
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "marketing.read"

    def get(self, request):
        try:
            days = max(1, min(90, int(request.query_params.get("days", 30))))
        except (TypeError, ValueError):
            days = 30
        today = date.today()
        start = today - timedelta(days=days - 1)
        rows = CampaignDailyMetrics.objects.filter(
            date__gte=start, date__lte=today,
        ).select_related("campaign", "campaign__source")

        # Totals + per-campaign rollup
        total_spend = Decimal("0")
        total_impressions = 0
        total_clicks = 0
        total_conversions = 0
        per_campaign: dict = {}
        per_day: dict = {}

        for r in rows:
            total_spend += r.spend
            total_impressions += r.impressions
            total_clicks += r.clicks
            total_conversions += r.conversions

            key = str(r.campaign.id)
            bucket = per_campaign.setdefault(key, {
                "campaign_id": key,
                "campaign": r.campaign.name,
                "source": r.campaign.source.name if r.campaign.source_id else "—",
                "spend": Decimal("0"), "impressions": 0,
                "clicks": 0, "conversions": 0,
                "currency": r.currency or r.campaign.currency or "",
            })
            bucket["spend"] += r.spend
            bucket["impressions"] += r.impressions
            bucket["clicks"] += r.clicks
            bucket["conversions"] += r.conversions

            d_key = r.date.isoformat()
            day = per_day.setdefault(d_key, {
                "date": d_key, "spend": Decimal("0"),
                "impressions": 0, "clicks": 0, "conversions": 0,
            })
            day["spend"] += r.spend
            day["impressions"] += r.impressions
            day["clicks"] += r.clicks
            day["conversions"] += r.conversions

        def finalize(b):
            spend = b["spend"]
            clicks = b["clicks"]
            convs = b["conversions"]
            imps = b["impressions"]
            b["spend"] = str(spend)
            b["cpc"] = str((spend / clicks).quantize(Decimal("0.01"))) if clicks else None
            b["cpm"] = str((spend / imps * 1000).quantize(Decimal("0.01"))) if imps else None
            b["cpa"] = str((spend / convs).quantize(Decimal("0.01"))) if convs else None
            b["ctr_pct"] = round(clicks / imps * 100, 2) if imps else None
            return b

        campaigns = sorted(
            (finalize(b) for b in per_campaign.values()),
            key=lambda x: -Decimal(x["spend"]),
        )
        days_series = sorted(
            [{**d, "spend": str(d["spend"])} for d in per_day.values()],
            key=lambda x: x["date"],
        )

        return Response({
            "from": start.isoformat(),
            "to": today.isoformat(),
            "totals": {
                "spend": str(total_spend),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "conversions": total_conversions,
                "cpc": str((total_spend / total_clicks).quantize(Decimal("0.01")))
                if total_clicks else None,
                "cpa": str((total_spend / total_conversions).quantize(Decimal("0.01")))
                if total_conversions else None,
                "ctr_pct": round(total_clicks / total_impressions * 100, 2)
                if total_impressions else None,
            },
            "campaigns": campaigns,
            "days": days_series,
        })
