"""
Duplicate detection (Part 17 control #7).

Default rule: match on normalised phone exact AND, independently, on
normalised email exact. Returns the list of existing records matching
either — never merges automatically.
"""
from __future__ import annotations

from django.db.models import Q

from apps.core.normalisation import normalise_email, normalise_phone
from apps.leads.models import Lead


def find_duplicate_leads(*, phone: str | None, email: str | None,
                         exclude_id: str | None = None):
    pn = normalise_phone(phone)
    en = normalise_email(email)
    if not pn and not en:
        return Lead.objects.none()
    q = Q()
    if pn:
        q |= Q(phone_normalised=pn)
    if en:
        q |= Q(email_normalised=en)
    qs = Lead.objects.filter(q)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs
