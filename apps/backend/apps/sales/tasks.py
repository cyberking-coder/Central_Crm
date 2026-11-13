"""Celery tasks for the sales app."""
from __future__ import annotations

import logging

from celery import shared_task

from .services.followups import sweep_overdue_followups

log = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60,
             name="apps.sales.tasks.sweep_overdue_followups_task")
def sweep_overdue_followups_task(self):
    try:
        count = sweep_overdue_followups()
        log.info("sweep_overdue_followups emitted %s notifications", count)
        return count
    except Exception as exc:  # pragma: no cover
        log.exception("sweep_overdue_followups failed")
        raise self.retry(exc=exc)
