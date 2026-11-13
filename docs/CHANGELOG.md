# Changelog

## [Unreleased]

### Phase 5 — Management Dashboard
- apps/analytics/services.py: single-source KPI formulas (leads/activities/
  followups/tasks/customers, by day and week) with uniform
  employee/department/source filters; DST-safe via company TZ helpers.
- Endpoints: GET /api/v1/analytics/{dashboard/today, dashboard/weekly,
  leaderboard} — gated by reports.read.
- Reconciliation test: API payload matches service payload field-by-field.
- Performance tests: assertNumQueries ≤ 25 on today endpoint (Part 17 #9).
- Frontend: real Dashboard page (10 Today KPIs, 5 Weekly, leads-by-source,
  salesperson leaderboard) with drill-down links.

### Phase 4 — Sales, Tasks & Notifications
- sales.SalesActivity, sales.FollowUp, tasks.Task, notifications.Notification.
- Permissions seed +3 codes (sales.followup.read/manage, notifications.read).
- Services: activity logging updates last_contacted + customer timeline;
  follow-up complete/cancel; task complete; idempotent overdue sweeps.
- Lead assignment now sends a notification to the assignee.
- APIs: /sales/activities, /sales/followups (+ complete/cancel),
  /tasks (+ complete/mine), /notifications (+ mark_read/all/unread_count).
- Celery broker (Redis) + worker + beat added to docker-compose;
  sweep tasks every 5 minutes (Part 17 #8). Management commands available
  for cron-based deploys.
- Frontend: notification bell, /tasks page with My/Overdue/All tabs,
  activity + follow-up panel on lead detail.

### Phase 3 — Leads & Customers
(See previous entry.)

### Phase 2 — Authentication & Access Control
(See previous entry.)

### Phase 1 — Technical foundation
(See previous entry.)
