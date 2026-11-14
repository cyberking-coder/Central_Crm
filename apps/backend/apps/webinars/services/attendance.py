from __future__ import annotations

from datetime import datetime

from django.db import transaction

from apps.audit.services import record_audit

from ..models import WebinarAttendance


@transaction.atomic
def record_attendance(*, attendance: WebinarAttendance,
                      status: str,
                      joined_at: datetime | None = None,
                      left_at: datetime | None = None,
                      duration_minutes: int | None = None,
                      actor=None, request=None) -> WebinarAttendance:
    before = {"status": attendance.status,
              "joined_at": attendance.joined_at.isoformat()
              if attendance.joined_at else None,
              "left_at": attendance.left_at.isoformat()
              if attendance.left_at else None}
    attendance.status = status
    if joined_at is not None:
        attendance.joined_at = joined_at
    if left_at is not None:
        attendance.left_at = left_at
    if duration_minutes is not None:
        attendance.duration_minutes = duration_minutes
    elif attendance.joined_at and attendance.left_at:
        delta = (attendance.left_at - attendance.joined_at).total_seconds() / 60
        attendance.duration_minutes = max(0, int(delta))
    attendance.recorded_by = actor if getattr(
        actor, "is_authenticated", False) else None
    attendance.save()
    record_audit(
        actor=actor, action="webinar.attendance.updated",
        entity_type="WebinarAttendance", entity_id=str(attendance.pk),
        before=before, after={"status": attendance.status},
        request=request,
    )
    return attendance


def webinar_summary(webinar) -> dict:
    """Counts used by both the detail page and reports."""
    from ..models import WebinarRegistration
    regs = WebinarRegistration.objects.filter(webinar=webinar)
    total = regs.count()
    cancelled = regs.filter(status=WebinarRegistration.Status.CANCELLED).count()
    eligible = regs.filter(status=WebinarRegistration.Status.REGISTERED).count()

    att = WebinarAttendance.objects.filter(registration__webinar=webinar)
    attended = att.filter(status=WebinarAttendance.Status.ATTENDED).count()
    partial = att.filter(status=WebinarAttendance.Status.PARTIAL).count()
    absent = att.filter(status=WebinarAttendance.Status.ABSENT).count()
    rate = ((attended + partial) / eligible * 100.0) if eligible else 0.0
    return {
        "registrations_total": total,
        "registrations_cancelled": cancelled,
        "registrations_eligible": eligible,
        "attended": attended,
        "partial": partial,
        "absent": absent,
        "attendance_rate_pct": round(rate, 1),
    }
