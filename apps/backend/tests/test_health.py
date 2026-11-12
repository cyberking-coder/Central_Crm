"""Phase 1: health endpoint smoke test (no DB required for the route itself)."""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_returns_ok() -> None:
    client = APIClient()
    resp = client.get("/api/v1/health/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "central-crm-backend"
    assert body["database"]["reachable"] is True
    assert "company_timezone" in body
