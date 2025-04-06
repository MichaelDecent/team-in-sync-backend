from django.db import transaction
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from ..notifications.services import NotificationService
from .models import Project, ProjectMembership
from .serializers import (
    ProjectDetailSerializer,
    ProjectMembershipSerializer,
    ProjectSerializer,
)


# Create a FilterSet for Project filtering
class ProjectFilter(filters.FilterSet):
    role = filters.CharFilter(field_name="required_roles__role")
    skill = filters.NumberFilter(field_name="required_roles__required_skills__skill")
    member_of = filters.BooleanFilter(method="filter_member_of")

    class Meta:
        model = Project
        fields = ["status", "role", "skill"]

    def filter_member_of(self, queryset, name, value):
        user = self.request.user
        if value:  # Only filter if value is True
            return queryset.filter(team_members=user)
        return queryset


class IsProjectOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only project owners to edit or delete.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the project
        return obj.owner == request.user


@extend_schema_view(
    list=extend_schema(description="List all projects with optional filtering"),
    retrieve=extend_schema(description="Retrieve a specific project with details"),
    create=extend_schema(description="Create a project with roles and skills"),
    my_projects=extend_schema(
        description="List projects where the current user is a member"
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
    search_fields = ["title", "description", "required_roles__role"]

    def get_serializer_class(self):
        if self.action == "retrieve":
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
        """List projects where the current user is a member"""
        queryset = Project.objects.filter(team_members=request.user)

        # Apply filters from query params
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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

    @action(detail=False, methods=["get"])
    def my_memberships(self, request):
        """Endpoint to get current user's project memberships"""
        memberships = ProjectMembership.objects.filter(user=request.user)
        serializer = self.get_serializer(memberships, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a membership (join request)"""
        response = super().create(request, *args, **kwargs)

        # Send notification to project owner
        membership = ProjectMembership.objects.get(id=response.data["id"])
        NotificationService.create_join_request_notification(membership)

        return response

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """Update membership status (accept/reject)"""
        membership = self.get_object()
        status = request.data.get("status")

        # Only project owner can update status
        if request.user != membership.project.owner:
            return Response(
                {"detail": "Only project owner can update membership status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership.status = status
        membership.save()

        # Send notification to requesting user
        accepted = status == "approved"
        NotificationService.create_request_response_notification(membership, accepted)

        serializer = self.get_serializer(membership)
        return Response(serializer.data)
