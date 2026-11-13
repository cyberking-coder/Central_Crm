from __future__ import annotations

from datetime import date as date_type, datetime
from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasPermissionCode
from apps.core.timezones import company_tz, company_week_range_utc, now_company

from .services import (
    Filters,
    salesperson_leaderboard,
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
