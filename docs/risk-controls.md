# Part 17 — Mandatory Engineering Risk Controls

Live status index.

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | ✅ enforced | ADR 0001; all Phase 2 schema in committed migrations (`accounts/0001`, `accounts/0002_seed_rbac`, `departments/0001`, `employees/0001`, `employees/0002_employee_department`, `audit/0001`) |
| 2 | Centralised financial calculations | ⏳ Phase 7 | `apps/analytics/services.py` reserved |
| 3 | Permission enforcement matrix | ✅ landed | `apps/accounts/permissions.HasPermissionCode`; `tests/test_permission_matrix.py` (role × code parametrised) + `tests/test_auth.py` |
| 4 | Webhook idempotency | ⏳ Phase 7/9 | `apps/integrations/` scaffolded |
| 5 | Data retention & deletion | ✅ scaffolded | `Employee.user` PROTECT; `Department.manager` SET_NULL; `AuditLog` admin view-only (no add/edit/delete); `SoftDeleteModel` mixin; financial PROTECT lands in Phase 7 |
| 6 | Timezone correctness | ✅ | `apps/core/timezones.py`; `tests/test_timezones.py` |
| 7 | Duplicate detection | ⏳ Phase 3 | — |
| 8 | Background job reliability | ⏳ Phase 4 | — |
| 9 | Dashboard performance | ⏳ Phase 5 | — |
| 10 | Export & data security | 🟡 sanitiser + CSRF on mutations | `apps/core/exports.py`; CSRF enforced for all POSTs; permission mixin lands with first export endpoint in Phase 3 |
| 11 | Verification | ✅ ongoing | Phase Completion Report §12 |

Legend: ✅ landed · 🟡 partial · ⏳ scheduled · ❌ gap.
