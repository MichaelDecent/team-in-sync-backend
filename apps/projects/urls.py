from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectMembershipViewSet, ProjectViewSet, FavoriteProjectViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"memberships", ProjectMembershipViewSet, basename="memberships")
router.register(r"favorites", FavoriteProjectViewSet, basename="favorites")

urlpatterns = [
    path("", include(router.urls)),
]
