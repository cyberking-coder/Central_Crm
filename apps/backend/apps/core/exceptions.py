"""DRF exception handler with consistent envelope."""
from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


def drf_exception_handler(exc, context) -> Response | None:
    response = drf_default_handler(exc, context)
    if response is None:
        return None
    request = context.get("request")
    rid = getattr(request, "correlation_id", None) if request else None
    response.data = {
        "error": {
            "status": response.status_code,
            "detail": response.data,
        },
        "request_id": rid,
    }
    return response
