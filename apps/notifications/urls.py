from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
]