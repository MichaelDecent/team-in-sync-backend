from django.urls import path

from .views import (
    MyMembershipsView,
    MyProjectsView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectMembershipDetailView,
    ProjectMembershipListCreateView,
    ProjectRoleDetailView,
    ProjectRoleListCreateView,
)

app_name = "projects"

urlpatterns = [
    # Project endpoints
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    # Project roles endpoints
    path(
        "<int:project_id>/roles/",
        ProjectRoleListCreateView.as_view(),
        name="project-role-list-create",
    ),
    path(
        "<int:project_id>/roles/<int:pk>/",
        ProjectRoleDetailView.as_view(),
        name="project-role-detail",
    ),
    # Project memberships endpoints
    path(
        "<int:project_id>/memberships/",
        ProjectMembershipListCreateView.as_view(),
        name="project-membership-list-create",
    ),
    path(
        "memberships/<int:pk>/",
        ProjectMembershipDetailView.as_view(),
        name="project-membership-detail",
    ),
    # User-specific endpoints
    path("my/", MyProjectsView.as_view(), name="my-projects"),
    path("my/memberships/", MyMembershipsView.as_view(), name="my-memberships"),
]
