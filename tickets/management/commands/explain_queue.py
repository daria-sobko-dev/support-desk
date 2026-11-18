from django.core.management.base import BaseCommand
from django.db import connection

from tickets.models import Ticket


class Command(BaseCommand):
    help = "Show the database query plan for the main support queue query."

    def handle(self, *args, **options):
        qs = Ticket.objects.filter(status="open", priority="high").order_by("-created_at")[:20]
        self.stdout.write(f"Query:\n{qs.query}\n")
        if connection.vendor == "postgresql":
            plan = qs.explain(analyze=True, buffers=True)
        else:
            plan = qs.explain()
        self.stdout.write(f"Plan ({connection.vendor}):\n{plan}")
