"""CSV import for leads. Validates rows; reports failures without aborting."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from django.db import transaction

from apps.audit.services import record_audit
from apps.core.normalisation import normalise_email, normalise_phone
from apps.leads.models import Lead
from apps.leads.services.duplicate_detection import find_duplicate_leads
from apps.marketing.models import LeadSource

REQUIRED_COLUMNS = {"full_name"}
OPTIONAL_COLUMNS = {"phone", "email", "source", "interested_product",
                    "notes", "priority"}


@dataclass
class ImportReport:
    total_rows: int = 0
    created: int = 0
    duplicates_skipped: int = 0
    failed: list[dict] = field(default_factory=list)


def import_leads_csv(*, file_obj, actor, request=None,
                     skip_duplicates: bool = True) -> ImportReport:
    text = file_obj.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    columns = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    report = ImportReport()
    sources_by_slug = {s.slug: s for s in LeadSource.objects.all()}

    with transaction.atomic():
        for i, row in enumerate(reader, start=2):  # header is row 1
            report.total_rows += 1
            name = (row.get("full_name") or "").strip()
            if not name:
                report.failed.append({"row": i, "error": "full_name required"})
                continue

            phone = (row.get("phone") or "").strip()
            email = (row.get("email") or "").strip()
            pn = normalise_phone(phone)
            en = normalise_email(email)

            if skip_duplicates and (pn or en):
                dupes = find_duplicate_leads(phone=phone, email=email)
                if dupes.exists():
                    report.duplicates_skipped += 1
                    continue

            source = None
            source_key = (row.get("source") or "").strip().lower()
            if source_key:
                source = sources_by_slug.get(source_key)

            priority = (row.get("priority") or "medium").strip().lower()
            if priority not in dict(Lead.Priority.choices):
                priority = Lead.Priority.MEDIUM

            Lead.objects.create(
                full_name=name,
                phone=phone,
                phone_normalised=pn,
                email=email,
                email_normalised=en,
                source=source,
                interested_product=(row.get("interested_product") or "").strip(),
                priority=priority,
                notes=(row.get("notes") or "").strip(),
                created_by=actor if getattr(actor, "is_authenticated", False) else None,
            )
            report.created += 1

    record_audit(
        actor=actor, action="leads.imported", entity_type="Lead",
        extra={
            "created": report.created,
            "duplicates_skipped": report.duplicates_skipped,
            "failed": len(report.failed),
        },
        request=request,
    )
    return report
