from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectMembershipListView,
    ProjectMembershipCreateView,
    ProjectMembershipStatusUpdateView,
    ProjectViewSet,
    FavoriteProjectViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"favorites", FavoriteProjectViewSet, basename="favorites")

urlpatterns = [
    # Project memberships
    path("memberships/", ProjectMembershipListView.as_view(), name="membership-list"),
    path(
        "memberships/join/",
        ProjectMembershipCreateView.as_view(),
        name="membership-create",
    ),
    path(
        "memberships/<int:membership_id>/status/",
        ProjectMembershipStatusUpdateView.as_view(),
        name="membership-update-status",
    ),
    # Include router URLs
    path("", include(router.urls)),
]
