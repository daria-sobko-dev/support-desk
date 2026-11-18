import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Article, Incident, Ticket

TITLES = [
    "Site returns 502 Bad Gateway",
    "Cannot log in after password reset",
    "Checkout page is slow",
    "Email notifications not delivered",
    "File upload fails with 413",
    "Report export times out",
]


class Command(BaseCommand):
    help = "Fill the database with demo tickets, incidents and knowledge base articles."

    def add_arguments(self, parser):
        parser.add_argument("--tickets", type=int, default=200)

    def handle(self, *args, **options):
        now = timezone.now()
        tickets = [
            Ticket(
                title=random.choice(TITLES),
                customer_email=f"user{i}@example.com",
                channel=random.choice(Ticket.Channel.values),
                status=random.choice(Ticket.Status.values),
                priority=random.choice(Ticket.Priority.values),
            )
            for i in range(options["tickets"])
        ]
        Ticket.objects.bulk_create(tickets, batch_size=1000)

        incident = Incident.objects.create(
            title="API errors after deploy",
            severity=Incident.Severity.SEV2,
            started_at=now - timedelta(hours=3),
            resolved_at=now - timedelta(hours=2),
            impact="About 20% of API requests returned 500 for one hour.",
            root_cause="A migration added a column without a default; old workers crashed on insert.",
        )
        incident.tickets.set(Ticket.objects.filter(title=TITLES[0])[:5])

        Article.objects.get_or_create(
            title="502 Bad Gateway from Nginx",
            defaults={
                "problem": "Nginx returns 502 when the app server is down or too slow.",
                "solution": "Check `docker compose ps` and app logs, then the upstream timeout in Nginx.",
                "tags": "nginx,502,gunicorn",
            },
        )
        Article.objects.get_or_create(
            title="Slow ticket queue",
            defaults={
                "problem": "Listing open tickets is slow on a large table.",
                "solution": "Run `manage.py explain_queue` and make sure ticket_queue_idx is used.",
                "tags": "postgresql,index,performance",
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Created {len(tickets)} tickets, 1 incident, KB articles."))
