# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete

## Phase 3 — Leads & Customers — 🚧 In progress

Delivered (backend):

- **Models**: `marketing.LeadSource`, `marketing.Campaign` (with UTM fields),
  `leads.Lead`, `leads.LeadAssignmentHistory`, `leads.LeadStatusHistory`,
  `customers.Customer`, `customers.CustomerTimelineEvent`. UUID PKs,
  explicit `on_delete`, `phone_normalised` / `email_normalised` indexed
  columns.
- **Seed**: 9 lead sources (Website, Facebook, Instagram, Google Ads,
  Referral, WhatsApp, Webinar, Manual, Other).
- **Services**:
  - `duplicate_detection.find_duplicate_leads` — matches on normalised
    phone OR email (Part 17 #7).
  - `assignment.assign_lead` — transactional, creates
    `LeadAssignmentHistory` + audit row.
  - `conversion.convert_lead_to_customer` — transactional, preserves
    lead history, creates timeline event.
  - `csv_import.import_leads_csv` — validates required columns,
    normalises, skips duplicates, reports per-row failures.
- **APIs** under `/api/v1/`:
  - `leads/` — CRUD + `assign`, `convert`, `export`, `import`,
    `duplicates`, `history` custom actions.
  - `customers/` — CRUD + `timeline`, `export`.
  - `lead-sources/`, `campaigns/` CRUD.
- **Permissions**: per-action `HasPermissionCode` map; Salesperson queryset
  scoping (only assigned leads/customers visible).
- **CSV**: all exports go through `apps/core/exports.write_csv` sanitiser
  (Part 17 #10 ✅); export endpoints require `*.export` permission; every
  export emits an audit row.
- **Audit**: lead created/updated/status_changed/assigned/converted/
  deleted/imported/exported; same for customers.
- **Migrations**: 4 new (marketing/0001, marketing/0002 seed,
  customers/0001, leads/0001).

Delivered (frontend):

- Role-aware nav in `(app)` layout.
- `/leads` list with search + status filter + CSV export button.
- `/leads/new` with inline duplicate warning on phone/email blur.
- `/leads/[id]` detail with status dropdown, Convert-to-Customer button,
  linked customer when converted, full status + assignment history.
- `/customers` list with CSV export button.
- `/customers/[id]` detail with profile + chronological timeline.
- Typed client (`lib/api-client.ts`) and server (`lib/api-server.ts`)
  fetchers.

Tests added:

- `tests/test_duplicate_detection.py` — phone/email normalisation,
  match-by-phone, match-by-email, exclude-self, empty-criteria.
- `tests/test_leads_api.py` — 15 cases: CRUD, permission denials,
  salesperson scoping, assignment history + audit, conversion
  (success, repeat rejected, lost rejected), duplicates endpoint,
  CSV export (sanitised + permission-gated), CSV import (success,
  duplicates skipped, failures reported, missing column rejected),
  history endpoint.

Exit criteria:

- [x] Lead CRUD + assign + convert end-to-end works
- [x] Customer timeline shows conversion
- [x] Duplicate detection prevents and reports dupes
- [x] CSV import reports per-row outcomes
- [x] CSV export sanitised + permission-gated
- [x] Salesperson sees only their own leads
- [x] Every mutation audited
