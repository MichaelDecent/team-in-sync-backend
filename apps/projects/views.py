from django.db import transaction
from django.db.models import Q
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from core.utils.api_response import APIResponse

from ..notifications.services import NotificationService
from .models import Project, ProjectMembership, FavoriteProject
from .serializers import (
    ProjectDetailSerializer,
    ProjectMembershipSerializer,
    ProjectSerializer,
    FavoriteProjectSerializer,
)


class ProjectFilter(filters.FilterSet):
    role = filters.CharFilter(
        field_name="required_roles__role__name",
        lookup_expr="istartswith",
        label="role name",
    )
    skill = filters.CharFilter(
        field_name="required_roles__required_skills__skill__name",
        lookup_expr="istartswith",
        label="skill name",
    )
    member_of = filters.BooleanFilter(method="filter_member_of")

    class Meta:
        model = Project
        fields = ["status", "role", "skill"]

    def filter_member_of(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(Q(team_members=user) | Q(owner=user)).distinct()
        return queryset


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only project owners to edit or delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


@extend_schema_view(
    list=extend_schema(description="List all projects with optional filtering"),
    retrieve=extend_schema(description="Retrieve a specific project with details"),
    create=extend_schema(description="Create a project with roles and skills"),
    my_projects=extend_schema(
        description="List projects where the current user is a member"
    ),
    add_to_favorites=extend_schema(description="Add a project to user's favorites"),
    remove_from_favorites=extend_schema(
        description="Remove a project from user's favorites"
    ),
)
@extend_schema(tags=["Projects"])
class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing projects.
    Includes endpoint for creating projects with roles and skills.
    Supports filtering by role, skill, status, and user membership.
    """

    queryset = Project.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = ProjectFilter
    search_fields = [
        "title",
        "description",
        "required_roles__role__name",
        "required_roles__required_skills__skill__name",
    ]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ProjectDetailSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a project with nested roles and skills"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["get"])
    def my_projects(self, request):
        """List projects where the current user is a member or an owner"""
        queryset = Project.objects.filter(
            Q(team_members=request.user) | Q(owner=request.user)
        ).distinct()

        queryset = self.filter_queryset(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_to_favorites(self, request, pk=None):
        """Add a project to user's favorites"""
        project = self.get_object()
        user = request.user

        # Check if already favorited
        if FavoriteProject.objects.filter(user=user, project=project).exists():
            return APIResponse.error(message="Project is already in your favorites")

        # Add to favorites
        FavoriteProject.objects.create(user=user, project=project)
        return APIResponse.success(message="Project added to favorites")

    @action(detail=True, methods=["delete"])
    def remove_from_favorites(self, request, pk=None):
        """Remove a project from user's favorites"""
        project = self.get_object()
        user = request.user

        try:
            favorite = FavoriteProject.objects.get(user=user, project=project)
            favorite.delete()
            return APIResponse.success(message="Project removed from favorites")
        except FavoriteProject.DoesNotExist:
            return APIResponse.error(message="Project is not in your favorites")


@extend_schema_view(
    list=extend_schema(description="List user's favorite projects"),
    create=extend_schema(description="Add a project to favorites"),
    destroy=extend_schema(description="Remove a project from favorites"),
)
@extend_schema(tags=["Favorite Projects"])
class FavoriteProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user favorite projects"""

    serializer_class = FavoriteProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        """Filter to only show current user's favorites"""
        return FavoriteProject.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Add a project to favorites"""
        project_id = request.data.get("project")
        if not project_id:
            return APIResponse.error(message="Project ID is required")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return APIResponse.error(message="Project not found")

        # Check if already favorited
        if FavoriteProject.objects.filter(user=request.user, project=project).exists():
            return APIResponse.error(message="Project is already in your favorites")

        # Add to favorites
        favorite = FavoriteProject.objects.create(user=request.user, project=project)
        serializer = self.get_serializer(favorite)
        return APIResponse.success(
            data=serializer.data, message="Project added to favorites"
        )

    def destroy(self, request, *args, **kwargs):
        """Remove a project from favorites"""
        favorite = self.get_object()
        favorite.delete()
        return APIResponse.success(message="Project removed from favorites")


@extend_schema(tags=["Projects Memberships"])
class ProjectMembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project memberships.
    """

    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter memberships based on query params"""
        queryset = ProjectMembership.objects.all()

        project_id = self.request.query_params.get("project", None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        user_id = self.request.query_params.get("user", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a membership (join request)"""
        response = super().create(request, *args, **kwargs)

        membership = ProjectMembership.objects.get(id=response.data["id"])
        NotificationService.create_join_request_notification(membership)

        return response

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Update membership status (accept/reject)"""
        membership = self.get_object()
        status = request.data.get("status")

        if request.user != membership.project.owner:
            return Response(
                {"detail": "Only project owner can update membership status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership.status = status
        membership.save()

        accepted = status == "approved"
        NotificationService.create_request_response_notification(membership, accepted)

        serializer = self.get_serializer(membership)
        return Response(serializer.data)
