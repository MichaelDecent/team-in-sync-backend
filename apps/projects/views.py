from django.db import transaction
from django.db.models import Q
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.api_response import APIResponse

from ..notifications.services import NotificationService
from .models import Project, ProjectMembership, FavoriteProject
from .serializers import (
    ProjectDetailSerializer,
    ProjectMembershipSerializer,
    ProjectMembershipCreateSerializer,
    ProjectMembershipStatusUpdateSerializer,
    ProjectSerializer,
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
    http_method_names = ["get", "post", "patch", "delete"]

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
        return APIResponse.created(
            data=serializer.data,
            message="Project created successfully",
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


@extend_schema_view(
    list=extend_schema(description="List user's favorite projects"),
    create=extend_schema(description="Add a project to favorites"),
    destroy=extend_schema(description="Remove a project from favorites"),
)
@extend_schema(tags=["Favorite Projects"])
class FavoriteProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user favorite projects"""

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        """Filter to only show current user's favorite projects"""
        return Project.objects.filter(favorited_by__user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Add a project to favorites"""
        project_id = request.data.get("project")
        if not project_id:
            return APIResponse.error(message="Project ID is required")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return APIResponse.error(message="Project not found")

        if FavoriteProject.objects.filter(user=request.user, project=project).exists():
            return APIResponse.error(message="Project is already in your favorites")

        FavoriteProject.objects.create(user=request.user, project=project)
        serializer = self.get_serializer(project)
        return APIResponse.success(
            data=serializer.data, message="Project added to favorites"
        )

    def destroy(self, request, *args, **kwargs):
        """Remove a project from favorites"""
        project = self.get_object()
        FavoriteProject.objects.filter(user=request.user, project=project).delete()
        return APIResponse.success(message="Project removed from favorites")


@extend_schema(tags=["Project Memberships"])
class ProjectMembershipListView(APIView):
    """View for listing project memberships with optional filtering"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="List project memberships with optional filtering",
        parameters=[
            OpenApiParameter(
                name="project",
                description="Filter by project ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="user",
                description="Filter by user ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="status",
                description="Filter by status",
                required=False,
                type=str,
                enum=["pending", "approved", "rejected"],
            ),
        ],
    )
    def get(self, request):
        """List project memberships with optional filtering"""
        queryset = ProjectMembership.objects.all()

        project_id = request.query_params.get("project", None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        user_id = request.query_params.get("user", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        status_filter = request.query_params.get("status", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = ProjectMembershipSerializer(queryset, many=True)
        return APIResponse.success(data=serializer.data)


@extend_schema(tags=["Project Memberships"])
class ProjectMembershipCreateView(APIView):
    """View for joining a project by creating a membership request"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectMembershipCreateSerializer

    @extend_schema(description="Join a project by creating a membership request")
    def post(self, request):
        """Join a project by creating a membership request"""
        serializer = ProjectMembershipCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()

        NotificationService.create_join_request_notification(membership)

        response_serializer = ProjectMembershipSerializer(membership)
        return APIResponse.created(
            data=response_serializer.data,
            message="Project join request submitted successfully",
        )


@extend_schema(tags=["Project Memberships"])
class ProjectMembershipStatusUpdateView(APIView):
    """View for updating project membership status (approve/reject)"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectMembershipStatusUpdateSerializer

    @extend_schema(description="Approve or reject a membership request")
    def patch(self, request, membership_id):
        """Update membership status (approve/reject)"""
        try:
            membership = ProjectMembership.objects.get(id=membership_id)
        except ProjectMembership.DoesNotExist:
            return APIResponse.not_found("Membership not found")

        serializer = ProjectMembershipStatusUpdateSerializer(
            membership, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        accepted = membership.status == "approved"
        NotificationService.create_request_response_notification(membership, accepted)

        response_serializer = ProjectMembershipSerializer(membership)
        status_message = "approved" if accepted else "rejected"
        return APIResponse.success(
            data=response_serializer.data,
            message=f"Membership request {status_message} successfully",
        )
