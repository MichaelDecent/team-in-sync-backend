from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Project, ProjectMembership, ProjectRole
from .permissions import IsProjectOwner, IsProjectOwnerOrReadOnly
from .serializers import (
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectMembershipCreateSerializer,
    ProjectMembershipSerializer,
    ProjectMembershipUpdateSerializer,
    ProjectRoleCreateSerializer,
    ProjectRoleSerializer,
)


@extend_schema(tags=["Projects"])
class ProjectListCreateView(generics.ListCreateAPIView):
    """View for listing and creating projects"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectListSerializer

    def get_queryset(self):
        """Get projects based on query parameters"""
        queryset = Project.objects.all()

        # Filter by status if provided
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by owner if provided
        owner_param = self.request.query_params.get("owner")
        if owner_param:
            queryset = queryset.filter(owner_id=owner_param)

        # Filter by role if provided
        role_param = self.request.query_params.get("role")
        if role_param:
            queryset = queryset.filter(required_roles__role=role_param).distinct()

        # Filter by skill if provided
        skill_param = self.request.query_params.get("skill")
        if skill_param:
            queryset = queryset.filter(
                required_roles__required_skills__skill_id=skill_param
            ).distinct()

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


@extend_schema(tags=["Projects"])
class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting projects"""

    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrReadOnly]
    serializer_class = ProjectDetailSerializer
    queryset = Project.objects.all()


@extend_schema(tags=["Project Roles"])
class ProjectRoleListCreateView(generics.ListCreateAPIView):
    """View for listing and creating project roles"""

    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]
    serializer_class = ProjectRoleSerializer

    def get_queryset(self):
        """Get roles for a specific project"""
        project_id = self.kwargs.get("project_id")
        return ProjectRole.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectRoleCreateSerializer
        return ProjectRoleSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs.get("project_id")
        context["project"] = get_object_or_404(Project, id=project_id)
        context["request"] = self.request
        return context

    def check_permissions(self, request):
        super().check_permissions(request)
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not request.user == project.owner and request.method != "GET":
            self.permission_denied(request)


@extend_schema(tags=["Project Roles"])
class ProjectRoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting project roles"""

    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]
    serializer_class = ProjectRoleSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectRole.objects.filter(project_id=project_id)

    def check_permissions(self, request):
        super().check_permissions(request)
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not request.user == project.owner and request.method != "GET":
            self.permission_denied(request)


@extend_schema(tags=["Project Memberships"])
class ProjectMembershipListCreateView(generics.ListCreateAPIView):
    """View for listing and creating project memberships"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectMembershipCreateSerializer
        return ProjectMembershipSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectMembership.objects.filter(project_id=project_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def check_permissions(self, request):
        super().check_permissions(request)
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if request.method == "GET" and not (request.user == project.owner):
            self.permission_denied(request)


@extend_schema(tags=["Project Memberships"])
class ProjectMembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting project memberships"""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProjectMembershipUpdateSerializer
        return ProjectMembershipSerializer

    def get_queryset(self):
        return ProjectMembership.objects.all()

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # Only project owner can update membership status
        if request.method in ["PUT", "PATCH"] and not request.user == obj.project.owner:
            raise PermissionDenied(
                "Only the project owner can update membership status"
            )
        # Only project owner or the member themselves can view or delete
        if not (request.user == obj.project.owner or request.user == obj.user):
            raise PermissionDenied(
                "You don't have permission to access this membership"
            )


@extend_schema(tags=["Projects"])
class MyProjectsView(generics.ListAPIView):
    """View for listing user's own projects"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        """Get projects owned by or joined by the current user"""
        user = self.request.user
        filter_type = self.request.query_params.get("type", "all")

        if filter_type == "owned":
            return Project.objects.filter(owner=user)
        elif filter_type == "member":
            return Project.objects.filter(
                team_members=user, projectmembership__status="approved"
            ).distinct()
        elif filter_type == "pending":
            return Project.objects.filter(
                team_members=user, projectmembership__status="pending"
            ).distinct()
        else:  # all
            owned = Project.objects.filter(owner=user)
            member = Project.objects.filter(
                team_members=user, projectmembership__status="approved"
            ).distinct()
            return (owned | member).distinct()


@extend_schema(tags=["Project Memberships"])
class MyMembershipsView(generics.ListAPIView):
    """View for listing user's project memberships"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectMembershipSerializer

    def get_queryset(self):
        """Get memberships of the current user"""
        user = self.request.user
        status_param = self.request.query_params.get("status")

        queryset = ProjectMembership.objects.filter(user=user)

        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset
