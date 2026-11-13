# Part 17 — Mandatory Engineering Risk Controls

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | ✅ | All migrations committed; ADR 0001 |
| 2 | Centralised calculations | 🟡 scaffolded for KPIs | `apps/analytics/services.py` is now the single source for every KPI. Finance calculations land here in Phase 7 — the pattern is already in place and tested. |
| 3 | Permission enforcement matrix | ✅ | `HasPermissionCode` applied per viewset and on analytics endpoints; `test_analytics.test_reports_read_permission_required` |
| 4 | Webhook idempotency | ⏳ Phase 7/9 | — |
| 5 | Data retention & deletion | ✅ scaffolded | PROTECT on finance-adjacent FKs; `AuditLog` admin read-only |
| 6 | Timezone correctness | ✅ | Analytics always goes through `company_day_range_utc` / `company_week_range_utc` |
| 7 | Duplicate detection | ✅ | `leads/services/duplicate_detection.py` + tests |
| 8 | Background job reliability | ✅ | Celery with retries + time limits; sweeps idempotent via DB dedup |
| 9 | Dashboard performance | ✅ landed | `assertNumQueries ≤ 25` on today endpoint, `≤ 20` on weekly in `test_analytics.py` |
| 10 | Export & data security | ✅ | `write_csv` sanitiser; `*.export` permissions |
| 11 | Verification | ✅ | Phase Completion Report §12 |
