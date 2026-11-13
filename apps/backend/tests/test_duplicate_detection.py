"""Part 17 control #7 — duplicate detection on normalised phone/email."""
from __future__ import annotations

import pytest

from apps.core.normalisation import normalise_email, normalise_phone
from apps.leads.models import Lead
from apps.leads.services.duplicate_detection import find_duplicate_leads


pytestmark = pytest.mark.django_db


def test_phone_normalisation_strips_formatting():
    assert normalise_phone("+91 (987) 654-3210") == "919876543210"
    assert normalise_phone("  987 654 3210 ") == "9876543210"
    assert normalise_phone(None) == ""
    assert normalise_phone("") == ""


def test_email_normalisation_lowercases_and_trims():
    assert normalise_email(" John.Doe@Example.COM ") == "john.doe@example.com"
    assert normalise_email(None) == ""


def test_find_duplicate_matches_by_phone():
    Lead.objects.create(full_name="A", phone="+91 987 654 3210",
                        phone_normalised="919876543210")
    dupes = find_duplicate_leads(phone="(91)987-6543210", email=None)
    assert dupes.count() == 1


def test_find_duplicate_matches_by_email():
    Lead.objects.create(full_name="B", email="x@y.com",
                        email_normalised="x@y.com")
    dupes = find_duplicate_leads(phone=None, email="X@Y.com")
    assert dupes.count() == 1


def test_find_duplicate_excludes_self():
    lead = Lead.objects.create(full_name="C", phone="999",
                               phone_normalised="999")
    dupes = find_duplicate_leads(phone="999", email=None,
                                 exclude_id=str(lead.pk))
    assert dupes.count() == 0


def test_no_criteria_returns_empty():
    Lead.objects.create(full_name="D")
    assert find_duplicate_leads(phone=None, email=None).count() == 0
