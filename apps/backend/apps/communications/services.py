"""Contact-matching helpers so integrations don't need UUIDs."""
from __future__ import annotations

from apps.core.normalisation import normalise_email, normalise_phone
from apps.customers.models import Customer
from apps.leads.models import Lead


def resolve_lead_or_customer(*, email: str = "", phone: str = ""):
    """
    Given a contact email/phone, find the Customer first (more specific),
    then fall back to Lead. Returns (lead, customer) tuple; either or
    both can be None.
    """
    en = normalise_email(email)
    pn = normalise_phone(phone)

    cust = None
    if en:
        cust = Customer.objects.filter(email_normalised=en).first()
    if cust is None and pn:
        cust = Customer.objects.filter(phone_normalised=pn).first()

    if cust is not None:
        return None, cust

    lead = None
    if en:
        lead = Lead.objects.filter(email_normalised=en).first()
    if lead is None and pn:
        lead = Lead.objects.filter(phone_normalised=pn).first()
    return lead, None
