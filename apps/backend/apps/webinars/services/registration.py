from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import Q

from apps.audit.services import record_audit
from apps.core.normalisation import normalise_email, normalise_phone
from apps.customers.models import CustomerTimelineEvent

from ..models import Webinar, WebinarAttendance, WebinarRegistration


class RegistrationError(Exception):
    """Raised when a registration can't be created (capacity / duplicate)."""


@transaction.atomic
def register_for_webinar(*, webinar: Webinar, full_name: str,
                         phone: str = "", email: str = "",
                         lead=None, customer=None, source=None,
                         external_ref: str = "",
                         actor=None, request=None) -> WebinarRegistration:
    pn = normalise_phone(phone)
    en = normalise_email(email)

    # Capacity check — only counts active (non-cancelled) registrations.
    if webinar.registration_limit > 0:
        active = webinar.registrations.filter(
            status=WebinarRegistration.Status.REGISTERED).count()
        if active >= webinar.registration_limit:
            raise RegistrationError("Webinar is at capacity.")

    # Explicit duplicate check (service-side) in addition to DB constraints,
    # so we return a clean error without hitting the unique-index exception
    # and we also match contacts that share only phone.
    if pn or en:
        q = Q()
        if en:
            q |= Q(email_normalised=en)
        if pn:
            q |= Q(phone_normalised=pn)
        if webinar.registrations.filter(q).filter(
                status=WebinarRegistration.Status.REGISTERED).exists():
            raise RegistrationError(
                "This contact is already registered for the webinar.")

    try:
        reg = WebinarRegistration.objects.create(
            webinar=webinar, lead=lead, customer=customer,
            full_name=full_name, phone=phone, phone_normalised=pn,
            email=email, email_normalised=en,
            registration_source=source,
            external_ref=external_ref,
            registered_by=actor if getattr(actor, "is_authenticated", False)
            else None,
        )
    except IntegrityError as exc:  # concurrent insert
        raise RegistrationError(
            "This contact is already registered for the webinar.") from exc

    WebinarAttendance.objects.create(registration=reg)

    if customer is not None:
        CustomerTimelineEvent.objects.create(
            customer=customer,
            kind=CustomerTimelineEvent.Kind.NOTE,
            summary=f"Registered for webinar: {webinar.title}",
            data={"webinar_id": str(webinar.pk),
                  "registration_id": str(reg.pk)},
            actor=actor if getattr(actor, "is_authenticated", False) else None,
        )

    record_audit(actor=actor, action="webinar.registration.created",
                 entity_type="WebinarRegistration", entity_id=str(reg.pk),
                 extra={"webinar_id": str(webinar.pk)}, request=request)
    return reg


@transaction.atomic
def cancel_registration(*, registration: WebinarRegistration,
                        actor=None, request=None) -> WebinarRegistration:
    if registration.status == WebinarRegistration.Status.CANCELLED:
        return registration
    registration.status = WebinarRegistration.Status.CANCELLED
    registration.save(update_fields=["status"])
    # Also mark attendance cancelled so reports don't count them absent.
    WebinarAttendance.objects.filter(registration=registration).update(
        status=WebinarAttendance.Status.CANCELLED)
    record_audit(actor=actor, action="webinar.registration.cancelled",
                 entity_type="WebinarRegistration", entity_id=str(registration.pk),
                 request=request)
    return registration
