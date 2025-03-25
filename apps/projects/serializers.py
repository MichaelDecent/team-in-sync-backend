from rest_framework import serializers

from apps.users.models.profile_models import Skill
from apps.users.serializers.auth_serializers import UserSerializer
from apps.users.serializers.profile_serializers import SkillSerializer

from .models import Project, ProjectMembership, ProjectRole, ProjectRoleSkill


class ProjectRoleSkillSerializer(serializers.ModelSerializer):
    """Serializer for ProjectRoleSkill model"""

    skill_details = SkillSerializer(source="skill", read_only=True)

    class Meta:
        model = ProjectRoleSkill
        fields = ("id", "skill", "skill_details")
        read_only_fields = ("id",)


class ProjectRoleSerializer(serializers.ModelSerializer):
    """Serializer for ProjectRole model"""

    role_display = serializers.CharField(source="get_role_display", read_only=True)
    required_skills = ProjectRoleSkillSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectRole
        fields = ("id", "role", "role_display", "number_required", "required_skills")
        read_only_fields = ("id",)


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMembership model"""

    user_details = UserSerializer(source="user", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = (
            "id",
            "user",
            "user_details",
            "role",
            "role_display",
            "status",
            "status_display",
            "joined_at",
        )
        read_only_fields = ("id", "joined_at")


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for listing projects"""

    owner_details = UserSerializer(source="owner", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "description",
            "owner",
            "owner_details",
            "status",
            "status_display",
            "created_at",
            "member_count",
        )
        read_only_fields = ("id", "created_at")

    def get_member_count(self, obj):
        """Get the count of approved team members"""
        return obj.team_members.filter(projectmembership__status="approved").count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed project view"""

    owner_details = UserSerializer(source="owner", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    required_roles = ProjectRoleSerializer(many=True, read_only=True)
    team_members = serializers.SerializerMethodField()
    pending_members = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "description",
            "owner",
            "owner_details",
            "status",
            "status_display",
            "required_roles",
            "team_members",
            "pending_members",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_team_members(self, obj):
        """Get approved team members"""
        memberships = ProjectMembership.objects.filter(project=obj, status="approved")
        return ProjectMembershipSerializer(memberships, many=True).data

    def get_pending_members(self, obj):
        """Get pending team members"""
        memberships = ProjectMembership.objects.filter(project=obj, status="pending")
        return ProjectMembershipSerializer(memberships, many=True).data


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects"""

    class Meta:
        model = Project
        fields = ("title", "description", "status")

    def create(self, validated_data):
        """Create a new project and set the owner"""
        user = self.context.get("request").user
        project = Project.objects.create(owner=user, **validated_data)
        return project


class ProjectRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project roles with associated skills"""

    skills = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Skill.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = ProjectRole
        fields = ("role", "number_required", "skills")

    def create(self, validated_data):
        """Create a new project role with associated skills"""
        skills = validated_data.pop("skills", [])
        project = self.context.get("project")

        if not project:
            raise serializers.ValidationError({"error": "Project is required"})

        # Check if this role already exists for the project
        if ProjectRole.objects.filter(
            project=project, role=validated_data["role"]
        ).exists():
            raise serializers.ValidationError(
                {"error": "This role already exists for this project"}
            )

        project_role = ProjectRole.objects.create(project=project, **validated_data)

        # Add skills to the role
        for skill in skills:
            ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        return project_role


class ProjectMembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project memberships (joining projects)"""

    class Meta:
        model = ProjectMembership
        fields = ("project", "role")

    def create(self, validated_data):
        """Create a new project membership"""
        user = self.context.get("request").user
        project = validated_data.get("project")
        role = validated_data.get("role")

        # Check if user already has the same role in this project
        if ProjectMembership.objects.filter(
            user=user, project=project, role=role
        ).exists():
            raise serializers.ValidationError(
                {"error": "You already applied for this role in this project"}
            )

        # Check if the role is available in the project
        if not ProjectRole.objects.filter(project=project, role=role).exists():
            raise serializers.ValidationError(
                {"error": "This role is not available in this project"}
            )

        return ProjectMembership.objects.create(user=user, **validated_data)


class ProjectMembershipUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating project membership status"""

    class Meta:
        model = ProjectMembership
        fields = ("status",)

    def validate_status(self, value):
        """Validate that status is one of the allowed values"""
        if value not in [status[0] for status in ProjectMembership.STATUS_CHOICES]:
            raise serializers.ValidationError("Invalid status")
        return value
