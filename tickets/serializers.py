from rest_framework import serializers

from .models import Article, Incident, Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id", "title", "description", "customer_email", "channel",
            "status", "priority", "assignee", "created_at", "updated_at", "resolved_at",
        ]
        read_only_fields = ["created_at", "updated_at", "resolved_at"]


class IncidentSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id", "title", "severity", "started_at", "resolved_at",
            "impact", "root_cause", "tickets", "is_open", "duration_minutes",
        ]

    def validate(self, attrs):
        started = attrs.get("started_at", getattr(self.instance, "started_at", None))
        resolved = attrs.get("resolved_at", getattr(self.instance, "resolved_at", None))
        if started and resolved and resolved < started:
            raise serializers.ValidationError({"resolved_at": "Cannot be earlier than started_at."})
        return attrs


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "problem", "solution", "tags", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
