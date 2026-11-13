"""Lead assignment with history + audit."""
from __future__ import annotations

from django.db import transaction

from apps.audit.services import record_audit
from apps.employees.models import Employee
from apps.leads.models import Lead, LeadAssignmentHistory
from apps.notifications.models import Notification
from apps.notifications.services import notify


@transaction.atomic
def assign_lead(*, lead: Lead, to_employee: Employee | None,
                actor, reason: str = "", request=None) -> Lead:
    from_employee = lead.assigned_to
    lead.assigned_to = to_employee
    if to_employee is None:
        lead.status = Lead.Status.UNASSIGNED
    elif lead.status in (Lead.Status.NEW, Lead.Status.UNASSIGNED):
        lead.status = Lead.Status.ASSIGNED
    lead.save(update_fields=["assigned_to", "status", "updated_at"])

    LeadAssignmentHistory.objects.create(
        lead=lead, from_employee=from_employee, to_employee=to_employee,
        assigned_by=actor if getattr(actor, "is_authenticated", False) else None,
        reason=reason,
    )
    record_audit(
        actor=actor, action="lead.assigned",
        entity_type="Lead", entity_id=str(lead.pk),
        before={"assigned_to": str(from_employee.pk) if from_employee else None},
        after={"assigned_to": str(to_employee.pk) if to_employee else None},
        extra={"reason": reason}, request=request,
    )
    recipient = getattr(to_employee, "user", None) if to_employee else None
    if recipient is not None:
        kind = (Notification.Kind.LEAD_REASSIGNED if from_employee
                else Notification.Kind.LEAD_ASSIGNED)
        notify(
            recipient=recipient, kind=kind,
            title=f"Lead assigned: {lead.full_name}",
            body=reason or "",
            related_kind="lead", related_id=lead.pk,
        )
    return lead
