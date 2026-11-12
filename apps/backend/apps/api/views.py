"""Phase 1 API views: health check only."""
from __future__ import annotations

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness + DB reachability. Unauthenticated by design."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        summary="Health check",
        description="Returns service status, DB reachability and configured timezone.",
        responses={200: dict},
    )
    def get(self, request: Request) -> Response:
        db_ok = True
        db_error: str | None = None
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except Exception as exc:  # pragma: no cover - surface in payload
            db_ok = False
            db_error = str(exc)

        payload = {
            "status": "ok" if db_ok else "degraded",
            "service": "central-crm-backend",
            "version": "1.0.0",
            "database": {"reachable": db_ok, "error": db_error},
            "company_timezone": settings.COMPANY_DEFAULT_TIMEZONE,
            "company_currency": settings.COMPANY_DEFAULT_CURRENCY,
        }
        http = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http)
