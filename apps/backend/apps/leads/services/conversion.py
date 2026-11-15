"""Lead-to-customer conversion that preserves the lead history."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.core.normalisation import normalise_email, normalise_phone
from apps.customers.models import Customer, CustomerTimelineEvent
from apps.integrations.outbound import fire_event
from apps.leads.models import Lead, LeadStatusHistory


class ConversionError(Exception):
    pass


@transaction.atomic
def convert_lead_to_customer(*, lead: Lead, actor, request=None) -> Customer:
    if lead.converted_customer_id:
        raise ConversionError("Lead has already been converted.")
    if lead.status == Lead.Status.LOST:
        raise ConversionError("Lost leads cannot be converted.")

    customer = Customer.objects.create(
        full_name=lead.full_name,
        phone=lead.phone,
        phone_normalised=normalise_phone(lead.phone),
        email=lead.email,
        email_normalised=normalise_email(lead.email),
        source=lead.source,
        assigned_to=lead.assigned_to,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
        notes=lead.notes,
    )

    prior = lead.status
    lead.status = Lead.Status.CONVERTED
    lead.converted_customer = customer
    lead.converted_at = timezone.now()
    lead.save(update_fields=[
        "status", "converted_customer", "converted_at", "updated_at"])

    LeadStatusHistory.objects.create(
        lead=lead, from_status=prior, to_status=Lead.Status.CONVERTED,
        changed_by=actor if getattr(actor, "is_authenticated", False) else None,
    )
    CustomerTimelineEvent.objects.create(
        customer=customer,
        kind=CustomerTimelineEvent.Kind.LEAD_CONVERTED,
        summary=f"Converted from lead {lead.full_name}",
        data={"lead_id": str(lead.pk)},
        actor=actor if getattr(actor, "is_authenticated", False) else None,
    )
    record_audit(
        actor=actor, action="lead.converted",
        entity_type="Lead", entity_id=str(lead.pk),
        after={"customer_id": str(customer.pk)}, request=request,
    )
    fire_event("lead.converted", {
        "lead_id": str(lead.pk),
        "customer_id": str(customer.pk),
        "full_name": customer.full_name,
    })
    fire_event("customer.created", {
        "customer_id": str(customer.pk),
        "full_name": customer.full_name,
        "email": customer.email,
        "phone": customer.phone,
    })
    return customer
