from django.contrib import admin

from .models import Article, Incident, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "status", "priority", "channel", "customer_email", "assignee", "created_at"]
    list_filter = ["status", "priority", "channel"]
    search_fields = ["title", "customer_email"]
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected tickets as resolved")
    def mark_resolved(self, request, queryset):
        for ticket in queryset:
            ticket.resolve()


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["title", "severity", "started_at", "resolved_at"]
    list_filter = ["severity"]
    filter_horizontal = ["tickets"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "tags", "updated_at"]
    search_fields = ["title", "problem", "tags"]
