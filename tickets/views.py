import logging

from django.db import DatabaseError, connection
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Article, Incident, Ticket
from .serializers import ArticleSerializer, IncidentSerializer, TicketSerializer

logger = logging.getLogger(__name__)


@require_GET
def health(request):
    """Liveness and database check for load balancers and Docker healthchecks."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("health check: database unavailable")
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


class TicketViewSet(viewsets.ModelViewSet):
    """Support queue. Filter with ?status=open&priority=high, search with ?q=."""

    queryset = Ticket.objects.select_related("assignee")
    serializer_class = TicketSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if status := params.get("status"):
            qs = qs.filter(status=status)
        if priority := params.get("priority"):
            qs = qs.filter(priority=priority)
        if q := params.get("q"):
            qs = qs.filter(Q(title__icontains=q) | Q(customer_email__icontains=q))
        return qs

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        ticket.resolve()
        logger.info("ticket resolved id=%s by=%s", ticket.pk, request.user)
        return Response(self.get_serializer(ticket).data)


class IncidentViewSet(viewsets.ModelViewSet):
    """Incident log. ?open=true shows incidents that are still ongoing."""

    queryset = Incident.objects.prefetch_related("tickets")
    serializer_class = IncidentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("open") == "true":
            qs = qs.filter(resolved_at__isnull=True)
        return qs


class ArticleViewSet(viewsets.ModelViewSet):
    """Knowledge base. Search with ?q= across title, problem and tags."""

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if q := self.request.query_params.get("q"):
            qs = qs.filter(Q(title__icontains=q) | Q(problem__icontains=q) | Q(tags__icontains=q))
        return qs
