"""
Celery application for Central CRM.

Part 17 #8: background jobs must be idempotent where practical, have retry
limits, log failures, and prevent duplicate side effects. The sweep tasks
below use database-side dedup so repeated runs produce no duplicate rows.
"""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("central_crm")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sweep-overdue-followups-every-5-min": {
        "task": "apps.sales.tasks.sweep_overdue_followups_task",
        "schedule": crontab(minute="*/5"),
    },
    "sweep-overdue-tasks-every-5-min": {
        "task": "apps.tasks.tasks.sweep_overdue_tasks_task",
        "schedule": crontab(minute="*/5"),
    },
}
