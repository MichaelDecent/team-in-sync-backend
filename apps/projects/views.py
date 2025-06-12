from django.db import transaction
from django.db.models import Q
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


class ProjectFilter(filters.FilterSet):
    # filter by Role.name
    role = filters.CharFilter(
        field_name="required_roles__role__name",
        lookup_expr="istartswith",
        label="role name",
    )
    # filter by Skill.name
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
