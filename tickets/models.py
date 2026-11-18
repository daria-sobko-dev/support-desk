from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    """A support request from a customer or a teammate."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        WAITING = "waiting", "Waiting for customer"
        RESOLVED = "resolved", "Resolved"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        CHAT = "chat", "Chat"
        PORTAL = "portal", "Portal"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    customer_email = models.EmailField()
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # The support queue is filtered by status and priority all day long,
            # newest first. See `manage.py explain_queue` for the query plan.
            models.Index(fields=["status", "priority", "-created_at"], name="ticket_queue_idx"),
            models.Index(fields=["customer_email"], name="ticket_customer_idx"),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} {self.title}"

    def resolve(self) -> None:
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])


class Incident(models.Model):
    """An outage or degradation: what happened, how bad, and why."""

    class Severity(models.TextChoices):
        SEV1 = "sev1", "SEV1: service down"
        SEV2 = "sev2", "SEV2: major feature broken"
        SEV3 = "sev3", "SEV3: minor impact"

    title = models.CharField(max_length=200)
    severity = models.CharField(max_length=4, choices=Severity.choices, default=Severity.SEV3)
    started_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    impact = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    tickets = models.ManyToManyField(Ticket, blank=True, related_name="incidents")

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.title}"

    @property
    def is_open(self) -> bool:
        return self.resolved_at is None

    @property
    def duration_minutes(self) -> int | None:
        if self.resolved_at is None:
            return None
        return int((self.resolved_at - self.started_at).total_seconds() // 60)


class Article(models.Model):
    """Knowledge base: known problems and how to fix them."""

    title = models.CharField(max_length=200)
    problem = models.TextField()
    solution = models.TextField()
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated, e.g. nginx,ssl")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title
