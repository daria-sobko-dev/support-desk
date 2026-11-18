from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from tickets.models import Article, Incident, Ticket


class HealthTests(TestCase):
    def test_health_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})


class ApiTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("agent", password="test-pass-123")
        self.api = APIClient()
        self.api.force_authenticate(self.user)


class AuthTests(TestCase):
    def test_api_requires_login(self):
        response = APIClient().get("/api/tickets/")
        self.assertEqual(response.status_code, 403)


class TicketApiTests(ApiTestCase):
    def test_create_ticket(self):
        response = self.api.post(
            "/api/tickets/",
            {"title": "Site is down", "customer_email": "a@example.com", "priority": "critical"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "open")

    def test_invalid_email_rejected(self):
        response = self.api.post("/api/tickets/", {"title": "x", "customer_email": "nope"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("customer_email", response.data)

    def test_filter_by_status_and_priority(self):
        Ticket.objects.create(title="a", customer_email="a@example.com", priority="high")
        Ticket.objects.create(title="b", customer_email="b@example.com", priority="low")
        Ticket.objects.create(title="c", customer_email="c@example.com", priority="high", status="resolved")
        response = self.api.get("/api/tickets/?status=open&priority=high")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "a")

    def test_search(self):
        Ticket.objects.create(title="Checkout is slow", customer_email="shop@example.com")
        Ticket.objects.create(title="Login error", customer_email="x@example.com")
        response = self.api.get("/api/tickets/?q=checkout")
        self.assertEqual(response.data["count"], 1)

    def test_resolve_action(self):
        ticket = Ticket.objects.create(title="a", customer_email="a@example.com")
        response = self.api.post(f"/api/tickets/{ticket.pk}/resolve/")
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.RESOLVED)
        self.assertIsNotNone(ticket.resolved_at)


class IncidentApiTests(ApiTestCase):
    def test_open_filter_and_duration(self):
        now = timezone.now()
        Incident.objects.create(title="ongoing", started_at=now)
        Incident.objects.create(title="done", started_at=now - timedelta(minutes=90), resolved_at=now)
        response = self.api.get("/api/incidents/?open=true")
        self.assertEqual(response.data["count"], 1)
        done = self.api.get("/api/incidents/").data["results"]
        durations = {i["title"]: i["duration_minutes"] for i in done}
        self.assertEqual(durations["done"], 90)

    def test_resolved_before_started_rejected(self):
        now = timezone.now()
        response = self.api.post(
            "/api/incidents/",
            {"title": "bad", "started_at": now.isoformat(), "resolved_at": (now - timedelta(hours=1)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class ArticleApiTests(ApiTestCase):
    def test_search_by_tag(self):
        Article.objects.create(title="502", problem="bad gateway", solution="check app", tags="nginx,502")
        Article.objects.create(title="Disk full", problem="no space", solution="clean logs", tags="linux")
        response = self.api.get("/api/articles/?q=nginx")
        self.assertEqual(response.data["count"], 1)
