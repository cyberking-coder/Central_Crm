# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete
## Phase 4 — Sales, Tasks & Notifications — ✅ Complete
## Phase 5 — Management Dashboard — ✅ Complete

## Phase 6 — Webinars — 🚧 In progress

Delivered (backend):

- **Models**: `webinars.Webinar`, `webinars.WebinarRegistration`,
  `webinars.WebinarAttendance`.
  - UUID PKs.
  - Partial unique constraints on `(webinar, email_normalised)` and
    `(webinar, phone_normalised)` — only applied when the normalised
    value is non-empty.
  - Attendance is a `OneToOneField` from registration (auto-created on
    registration).
  - Explicit `on_delete`: registration CASCADEs its attendance; leads /
    customers / sources are `SET_NULL` so webinar history survives
    archival.
- **Services**:
  - `register_for_webinar` — enforces capacity (ignoring cancelled rows),
    duplicate contact detection, creates attendance row, writes customer
    timeline event if linked, audits.
  - `cancel_registration` — flips status and marks attendance cancelled.
  - `record_attendance` — computes duration when both timestamps given,
    audits before/after.
  - `webinar_summary` — counts + attendance rate for stats endpoint.
- **API** under `/api/v1/webinars/`:
  - CRUD on webinars.
  - `POST /webinars/{id}/register/` — single-contact registration (safely
    returns 400 on capacity/duplicate).
  - `GET /webinars/{id}/registrations/` — list of registrations with
    inlined attendance status.
  - `GET /webinars/{id}/stats/` — summary (used by dashboard + reports).
  - `GET /webinars/registrations/` — flat list, filterable by webinar.
  - `PATCH /webinars/attendance/{id}/` — update attendance status +
    joined/left times; auto-derives `duration_minutes`.
- **Permissions**: per-action map using the existing `webinars.read`,
  `webinars.manage`, `webinars.attendance` codes (seeded in Phase 2).

Delivered (frontend):

- Nav adds **Webinars**.
- `/webinars` list with status, start time, host, capacity.
- `/webinars/new` form (validates end > start client-side via the input).
- `/webinars/[id]` detail:
  - 5 stat cards (registered / eligible / attended / absent / rate).
  - Registration panel: add contact, see live list, change attendance per
    row via dropdown.

Tests (`tests/test_webinars.py`, 10 cases):
- Capacity blocks third registration when limit=2.
- Cancelled rows free capacity.
- Unlimited (limit=0) allows many.
- Duplicate email (case-insensitive) rejected.
- Duplicate phone (post-normalisation) rejected.
- Same contact allowed across different webinars.
- API: create requires `webinars.manage`; end-before-start rejected;
  register returns 201; capacity returns 400.
- Stats endpoint reconciles counts and attendance %.
- Attendance update records an audit entry.

Exit criteria:

- [x] Registration capacity enforced and tested
- [x] Duplicate contact rejection + DB-level partial unique constraints
- [x] Attendance updates auditable
- [x] Stats reconcile with registrations/attendance
- [x] Permission-gated end-to-end
