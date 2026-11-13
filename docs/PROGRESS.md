# Progress log

## Phase 0 — Discovery & Architecture — ✅ Complete
## Phase 1 — Technical Foundation — ✅ Complete
## Phase 2 — Authentication & Access Control — ✅ Complete
## Phase 3 — Leads & Customers — ✅ Complete

## Phase 4 — Sales, Tasks & Notifications — 🚧 In progress

Delivered (backend):

- **Models**: `sales.SalesActivity`, `sales.FollowUp`, `tasks.Task`,
  `notifications.Notification`. UUID PKs, indexes on hot columns.
- **Permissions seed update**: `sales.followup.read`,
  `sales.followup.manage`, `notifications.read` added across the eight
  roles (migration `accounts/0003_add_phase4_permissions`).
- **Services**:
  - `sales/services/activities.record_activity` — updates
    `Lead.last_contacted_at`, writes `CustomerTimelineEvent`, audits.
  - `sales/services/followups` — `complete_followup`, `cancel_followup`,
    `sweep_overdue_followups` (idempotent dedup).
  - `tasks/services/tasks` — `complete_task`, `notify_task_assigned`,
    `sweep_overdue_tasks` (idempotent dedup).
  - Lead assignment now emits a notification to the assignee.
- **APIs** under `/api/v1/`:
  - `sales/activities/` CRUD (requires linked lead or customer).
  - `sales/followups/` CRUD + `complete`, `cancel` actions.
  - `tasks/` CRUD + `complete`, `mine` actions.
  - `notifications/` list + `mark_read`, `mark_all_read`, `unread_count`.
- **Celery (Part 17 #8)**:
  - `config/celery.py` with retry limits and soft/hard time limits.
  - `shared_task` definitions for the two sweeps.
  - Celery Beat schedule: every 5 minutes.
  - Also available as management commands: `sweep_followups`,
    `sweep_tasks` (so cron or ad-hoc runs work without Celery).
  - `docker-compose.yml` adds `redis`, `celery_worker`, `celery_beat`.
- **Audit**: sales.activity.created/updated, followup.created/completed/
  cancelled, task.created/updated/deleted/completed.

Delivered (frontend):

- Nav adds **Tasks**.
- Header adds **Notification bell**: polls `unread_count` every 30 s,
  dropdown lists latest, per-row mark-read + mark-all-read.
- `/tasks` with 3 tabs: *My tasks*, *Overdue*, *All*; inline Complete
  button.
- Lead detail now has an **Activity panel**: log activity, see recent
  activities, schedule follow-ups, complete follow-ups.

Tests:
- `tests/test_sales_api.py` — 7 cases: activity requires lead/customer,
  activity writes timeline, activity updates last_contacted_at,
  salesperson activity scoping, follow-up complete, overdue sweep
  idempotency, lead-assignment notification.
- `tests/test_tasks_api.py` — 5 cases: task assigned notification,
  salesperson task scoping, complete action, mine endpoint, overdue
  sweep idempotency.

Exit criteria:

- [x] Activities + follow-ups + tasks CRUD work end-to-end
- [x] Overdue sweeps emit at most one notification per (user, entity)
- [x] Notifications surface in the UI
- [x] Salesperson scoping holds for activities, follow-ups, and tasks
- [x] Celery broker + worker + beat wired in compose
