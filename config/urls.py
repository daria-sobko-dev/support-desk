from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tickets.views import ArticleViewSet, IncidentViewSet, TicketViewSet, health

router = DefaultRouter()
router.register("tickets", TicketViewSet)
router.register("incidents", IncidentViewSet)
router.register("articles", ArticleViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
