from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.customers.models import CustomerTimelineEvent

from ..models import SalesActivity


@transaction.atomic
def record_activity(*, activity: SalesActivity, actor, request=None) -> SalesActivity:
    """Post-create hook: update related lead last_contacted_at, emit timeline."""
    if activity.lead_id:
        activity.lead.last_contacted_at = activity.occurred_at
        activity.lead.save(update_fields=["last_contacted_at", "updated_at"])
    if activity.customer_id:
        CustomerTimelineEvent.objects.create(
            customer=activity.customer,
            kind=CustomerTimelineEvent.Kind.NOTE,
            summary=f"{activity.get_kind_display()} · {activity.outcome or '—'}",
            data={"activity_id": str(activity.pk),
                  "discussion_summary": activity.discussion_summary},
            actor=actor if getattr(actor, "is_authenticated", False) else None,
        )
    record_audit(actor=actor, action="sales.activity.created",
                 entity_type="SalesActivity", entity_id=str(activity.pk),
                 extra={"kind": activity.kind}, request=request)
    return activity
