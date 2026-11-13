from django.core.management.base import BaseCommand

from apps.tasks.services.tasks import sweep_overdue_tasks


class Command(BaseCommand):
    help = "Emit notifications for overdue tasks."

    def handle(self, *args, **opts):
        n = sweep_overdue_tasks()
        self.stdout.write(self.style.SUCCESS(f"Emitted {n} notification(s)."))
