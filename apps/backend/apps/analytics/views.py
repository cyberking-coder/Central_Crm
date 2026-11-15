from __future__ import annotations

from datetime import date as date_type, datetime
from uuid import UUID

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasPermissionCode
from apps.audit.services import record_audit
from apps.core.exports import write_csv
from apps.core.timezones import (
    company_day_range_utc,
    company_tz,
    company_week_range_utc,
    now_company,
)

from .services import (
    Filters,
    campaign_performance_report,
    collections_per_day,
    conversion_funnel,
    department_performance_report,
    leads_per_day,
    salesperson_leaderboard,
    source_performance_report,
    today_payload,
    weekly_payload,
)


def _parse_date(raw: str | None) -> date_type | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_uuid(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


def _filters_from(request) -> Filters:
    q = request.query_params
    return Filters(
        employee_id=_parse_uuid(q.get("employee")),
        department_id=_parse_uuid(q.get("department")),
        source_id=_parse_uuid(q.get("source")),
    )


class DashboardTodayView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    @extend_schema(
        summary="Today's KPI payload",
        parameters=[
            OpenApiParameter("date", str, required=False,
                             description="YYYY-MM-DD, company-local."),
            OpenApiParameter("employee", str, required=False),
            OpenApiParameter("department", str, required=False),
            OpenApiParameter("source", str, required=False),
        ],
        responses={200: dict},
    )
    def get(self, request):
        d = _parse_date(request.query_params.get("date"))
        payload = today_payload(d=d, f=_filters_from(request))
        payload["timezone"] = str(company_tz())
        return Response(payload)


class DashboardWeeklyView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    @extend_schema(
        summary="This week's KPI payload",
        parameters=[
            OpenApiParameter("date", str, required=False,
                             description="Any date in the target week."),
            OpenApiParameter("employee", str, required=False),
            OpenApiParameter("department", str, required=False),
            OpenApiParameter("source", str, required=False),
        ],
        responses={200: dict},
    )
    def get(self, request):
        d = _parse_date(request.query_params.get("date"))
        payload = weekly_payload(d=d, f=_filters_from(request))
        payload["timezone"] = str(company_tz())
        return Response(payload)


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    @extend_schema(
        summary="Salesperson leaderboard for a week",
        parameters=[
            OpenApiParameter("date", str, required=False),
            OpenApiParameter("limit", int, required=False),
        ],
        responses={200: list},
    )
    def get(self, request):
        d = _parse_date(request.query_params.get("date")) or now_company().date()
        start, end = company_week_range_utc(d)
        try:
            limit = max(1, min(50, int(request.query_params.get("limit", 10))))
        except (TypeError, ValueError):
            limit = 10
        return Response(salesperson_leaderboard(start, end, limit=limit))


def _range_from_query(request):
    """Resolve [start, end) company-local UTC range from query params.
    Supports: ?from=YYYY-MM-DD&to=YYYY-MM-DD, falls back to the current week.
    `to` is INCLUSIVE in user-facing semantics; we add 1 day for half-open."""
    from datetime import timedelta
    q = request.query_params
    d_from = _parse_date(q.get("from"))
    d_to = _parse_date(q.get("to"))
    if not d_from or not d_to:
        return company_week_range_utc(now_company().date())
    start, _ = company_day_range_utc(d_from)
    _, end = company_day_range_utc(d_to)
    return start, end


class SourceReportView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    def get(self, request):
        start, end = _range_from_query(request)
        return Response({
            "from": start.date().isoformat(),
            "to": (end.date() if hasattr(end, "date") else end).isoformat(),
            "rows": source_performance_report(start, end),
        })


class CampaignReportView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    def get(self, request):
        start, end = _range_from_query(request)
        return Response({
            "from": start.date().isoformat(),
            "to": (end.date() if hasattr(end, "date") else end).isoformat(),
            "rows": campaign_performance_report(start, end),
        })


class FunnelReportView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    def get(self, request):
        start, end = _range_from_query(request)
        funnel = conversion_funnel(start, end)
        return Response({
            "from": start.date().isoformat(),
            "to": (end.date() if hasattr(end, "date") else end).isoformat(),
            "stages": funnel,
        })


class DepartmentReportView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    def get(self, request):
        start, end = _range_from_query(request)
        return Response({
            "from": start.date().isoformat(),
            "to": (end.date() if hasattr(end, "date") else end).isoformat(),
            "rows": department_performance_report(start, end),
        })


class ChartsView(APIView):
    """Timeseries for dashboard charts (last 30 days by default)."""
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    def get(self, request):
        from datetime import timedelta
        today = now_company().date()
        start_d = today - timedelta(days=29)
        start, _ = company_day_range_utc(start_d)
        _, end = company_day_range_utc(today)
        return Response({
            "from": start.date().isoformat(),
            "to": today.isoformat(),
            "leads_per_day": leads_per_day(start, end),
            "collections_per_day": collections_per_day(start, end),
        })


class ReportExportView(APIView):
    """`GET /api/v1/analytics/reports/<kind>/export/` — CSV."""
    permission_classes = [IsAuthenticated, HasPermissionCode]
    required_permission = "reports.read"

    REPORTS = {
        "sources": (source_performance_report,
                    ["source", "leads", "qualified", "converted",
                     "conversion_pct", "attributed_revenue"]),
        "campaigns": (campaign_performance_report,
                      ["campaign", "source", "leads", "converted",
                       "spend", "attributed_revenue",
                       "cost_per_lead", "roi_pct"]),
        "departments": (department_performance_report,
                        ["department", "activities", "tasks_completed",
                         "conversions"]),
    }

    def get(self, request, kind: str):
        spec = self.REPORTS.get(kind)
        if spec is None:
            return Response({"detail": "Unknown report."}, status=404)
        func, cols = spec
        start, end = _range_from_query(request)
        rows_data = func(start, end)
        rows = [[r.get(c, "") for c in cols] for r in rows_data]
        data = write_csv(cols, rows)
        record_audit(actor=request.user, action="report.exported",
                     entity_type="Report", entity_id=kind,
                     extra={"count": len(rows)}, request=request)
        resp = HttpResponse(data, content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{kind}-report.csv"'
        return resp
