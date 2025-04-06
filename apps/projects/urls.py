from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectMembershipViewSet, ProjectViewSet

app_name = "projects"

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"memberships", ProjectMembershipViewSet, basename="memberships")

urlpatterns = [
    path("", include(router.urls)),
]
