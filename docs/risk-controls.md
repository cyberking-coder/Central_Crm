# Part 17 — Mandatory Engineering Risk Controls

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | ✅ | All 14 migrations committed; ADR 0001 |
| 2 | Centralised financial calculations | ⏳ Phase 7 | — |
| 3 | Permission enforcement matrix | ✅ | `HasPermissionCode` applied per viewset; `tests/test_permission_matrix.py` + endpoint tests (leads/customers/sales/tasks) |
| 4 | Webhook idempotency | ⏳ Phase 7/9 | — |
| 5 | Data retention & deletion | ✅ scaffolded | PROTECTs on finance-adjacent FKs (`Employee.user`, `Task.assignee`, `FollowUp.owner`); `AuditLog` admin read-only |
| 6 | Timezone correctness | ✅ | `apps/core/timezones.py` |
| 7 | Duplicate detection | ✅ | `apps/leads/services/duplicate_detection.py` + tests |
| 8 | Background job reliability | ✅ landed | Celery with `bind=True`, `max_retries=3`, `default_retry_delay=60`, soft/hard time limits; sweeps are DB-dedup idempotent; `test_sales_api.test_sweep_overdue_followups_emits_and_dedupes` + `test_tasks_api.test_overdue_sweep_emits_once` |
| 9 | Dashboard performance | ⏳ Phase 5 | — |
| 10 | Export & data security | ✅ | CSV goes through `write_csv` sanitiser; export permissions enforced |
| 11 | Verification | ✅ | Phase Completion Report §12 |
