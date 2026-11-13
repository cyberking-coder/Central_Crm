# Changelog

## [Unreleased]

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
