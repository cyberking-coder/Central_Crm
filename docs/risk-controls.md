# Part 17 — Mandatory Engineering Risk Controls

Live status index.

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | ✅ | All 10 migrations committed; ADR 0001 |
| 2 | Centralised financial calculations | ⏳ Phase 7 | — |
| 3 | Permission enforcement matrix | ✅ | `HasPermissionCode` applied per viewset with action→code maps; `tests/test_permission_matrix.py` + `test_leads_api.py` role-scope assertions |
| 4 | Webhook idempotency | ⏳ Phase 7/9 | — |
| 5 | Data retention & deletion | ✅ scaffolded | `AuditLog` admin read-only; `Employee.user` PROTECT; Lead → Customer SET_NULL preserves customer when lead archived |
| 6 | Timezone correctness | ✅ | `apps/core/timezones.py` |
| 7 | Duplicate detection | ✅ | `apps/core/normalisation.py`, `leads/services/duplicate_detection.py`, `/leads/duplicates/` endpoint, `tests/test_duplicate_detection.py` |
| 8 | Background job reliability | ⏳ Phase 4 | — |
| 9 | Dashboard performance | ⏳ Phase 5 | — |
| 10 | Export & data security | ✅ | Every CSV goes through `write_csv` sanitiser; `leads.export` / `customers.export` permissions enforced; `test_leads_api.test_export_csv_is_sanitised` + permission test |
| 11 | Verification | ✅ ongoing | Phase Completion Report §12 |
