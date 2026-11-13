"""Celery tasks for the tasks app."""
from __future__ import annotations

import logging

from celery import shared_task

from .services.tasks import sweep_overdue_tasks

log = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60,
             name="apps.tasks.tasks.sweep_overdue_tasks_task")
def sweep_overdue_tasks_task(self):
    try:
        count = sweep_overdue_tasks()
        log.info("sweep_overdue_tasks emitted %s notifications", count)
        return count
    except Exception as exc:  # pragma: no cover
        log.exception("sweep_overdue_tasks failed")
        raise self.retry(exc=exc)
