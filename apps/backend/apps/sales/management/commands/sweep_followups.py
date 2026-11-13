from django.core.management.base import BaseCommand

from apps.sales.services.followups import sweep_overdue_followups


class Command(BaseCommand):
    help = "Emit notifications for overdue follow-ups."

    def handle(self, *args, **opts):
        n = sweep_overdue_followups()
        self.stdout.write(self.style.SUCCESS(f"Emitted {n} notification(s)."))
