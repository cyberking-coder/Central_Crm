"""Request correlation ID middleware (Part 17 control #11 / audit)."""
from __future__ import annotations

import uuid

from django.utils.deprecation import MiddlewareMixin


class CorrelationIdMiddleware(MiddlewareMixin):
    """Attach a stable X-Request-ID to every request & response."""

    HEADER = "X-Request-ID"

    def process_request(self, request):
        rid = request.META.get("HTTP_X_REQUEST_ID") or uuid.uuid4().hex
        request.correlation_id = rid

    def process_response(self, request, response):
        rid = getattr(request, "correlation_id", None)
        if rid:
            response[self.HEADER] = rid
        return response
