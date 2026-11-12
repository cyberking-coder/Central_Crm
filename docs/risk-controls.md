# Part 17 — Mandatory Engineering Risk Controls

Live status index. Each control is implemented, documented, tested.

| # | Control | Status | Evidence |
|---|---|---|---|
| 1 | Django-only schema ownership | 🟡 scaffolded | `docs/decisions/0001-django-owns-schema.md`; CI drift check lands with first migration in Phase 2 |
| 2 | Centralised financial calculations | ⏳ Phase 7 | `apps/analytics/services.py` reserved |
| 3 | Permission enforcement matrix | ⏳ Phase 2 | Test matrix lands with auth |
| 4 | Webhook idempotency | ⏳ Phase 7/9 | `apps/integrations/` scaffolded |
| 5 | Data retention & deletion | 🟡 policy drafted | Soft-delete mixin in `apps/core/models.py`; `on_delete` rules land per model |
| 6 | Timezone correctness | ✅ implemented | `apps/core/timezones.py`; `tests/test_timezones.py` |
| 7 | Duplicate detection | ⏳ Phase 3 | — |
| 8 | Background job reliability | ⏳ Phase 4 | Celery introduced then |
| 9 | Dashboard performance | ⏳ Phase 5 | `assertNumQueries` tests land with dashboard |
| 10 | Export & data security | ✅ sanitiser + 🟡 permission mixin to follow | `apps/core/exports.py`; `tests/test_exports.py` |
| 11 | Verification | ✅ ongoing | Phase Completion Reports include this table |

Legend: ✅ landed · 🟡 partially landed · ⏳ scheduled · ❌ gap.
