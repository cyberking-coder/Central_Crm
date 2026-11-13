# Changelog

## [Unreleased]

### Phase 3 — Leads & Customers
- marketing.LeadSource + Campaign models (UTM fields); 9 default sources seeded.
- leads.Lead with 12 statuses, 3 priorities, assignment/status history tables.
- customers.Customer + CustomerTimelineEvent.
- Duplicate detection service (normalised phone/email) + `/leads/duplicates/`
  endpoint (Part 17 #7).
- Lead assignment service with history + audit.
- Lead → Customer conversion that preserves lead and emits timeline event.
- CSV import with validation + per-row reporting; CSV export sanitised
  through `apps/core/exports.write_csv` and gated by export permissions
  (Part 17 #10).
- Salesperson queryset scoping (only assigned records visible).
- Frontend: role-aware nav, /leads list with filters, /leads/new with
  inline duplicate warning, /leads/[id] detail with convert + status +
  history, /customers list and detail with timeline.

### Phase 2 — Authentication & Access Control
(See previous entry.)

### Phase 1 — Technical foundation
(See previous entry.)
