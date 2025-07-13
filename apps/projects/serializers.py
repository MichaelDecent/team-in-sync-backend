from rest_framework import serializers

from apps.users.models.auth_models import User
from apps.users.models.profile_models import Role, Skill

from .models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    FavoriteProject,
)


class FavoriteProjectSerializer(serializers.ModelSerializer):
    """Serializer for favorite projects"""

    project_details = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteProject
        fields = ["id", "project", "project_details", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_project_details(self, obj):
        """Get basic project information"""
        return {
            "id": obj.project.id,
            "title": obj.project.title,
            "description": obj.project.description,
            "status": obj.project.status,
            "owner": obj.project.owner.email,
            "created_at": obj.project.created_at,
        }


class ProjectRoleSkillSerializer(serializers.ModelSerializer):
    """Serializer for project role skill"""

    skill_name = serializers.CharField(source="skill.name", read_only=True)
    skill_input = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ProjectRoleSkill
        fields = ["id", "skill_name", "skill_input"]

    def create(self, validated_data):
        skill_name = validated_data.pop("skill_input", None)
        if skill_name and not validated_data.get("skill"):
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            validated_data["skill"] = skill
        return super().create(validated_data)


class ProjectRoleSerializer(serializers.ModelSerializer):
    """Serializer for project role with its required skills"""

    required_skills = ProjectRoleSkillSerializer(many=True, read_only=True)
    skills_input = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False, default=list
    )
    role_name = serializers.CharField(source="role.name", read_only=True)
    role_input = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ProjectRole
        fields = [
            "id",
            "role_input",
            "role_name",
            "number_required",
            "required_skills",
            "skills_input",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Only allow one of role or role_input"""
        if "role" in data and "role_input" in data:
            raise serializers.ValidationError(
                "Only provide one of 'role' or 'role_input', not both"
            )
        if not data.get("role_input"):
            raise serializers.ValidationError("role_input is required")
        return data

    def create(self, validated_data):
        skill_names = validated_data.pop("skills_input", [])
        role_name = validated_data.pop("role_input", None)

        # Handle role by name
        if role_name:
            role, _ = Role.objects.get_or_create(name=role_name)
            validated_data["role"] = role

        project_role = ProjectRole.objects.create(**validated_data)

        # Add skills by name
        for skill_name in skill_names:
            skill, _ = Skill.objects.get_or_create(name=skill_name)
            ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        return project_role


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project with its required roles"""

    required_roles = ProjectRoleSerializer(many=True, read_only=True)
    roles = serializers.ListField(
        child=ProjectRoleSerializer(), write_only=True, required=False
    )
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
            "owner",
            "required_roles",
            "roles",
            "is_favorited",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner", "is_favorited"]

    def get_is_favorited(self, obj):
        """Check if the current user has favorited this project"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        roles_data = validated_data.pop("roles", [])
        project = Project.objects.create(**validated_data)

        for role_data in roles_data:
            skill_names = role_data.pop("skills_input", [])
            role_name = role_data.pop("role_input", None)

            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                role_data["role"] = role

            project_role = ProjectRole.objects.create(project=project, **role_data)

            for skill_name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        return project


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for project membership"""

    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=ProjectRole.objects.all()
    )
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all()
    )
    project_id = serializers.PrimaryKeyRelatedField(
        source="project", queryset=Project.objects.all()
    )
    full_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = [
            "id",
            "user_id",
            "project_id",
            "full_name",
            "role_name",
            "profile_picture_url",
            "role_id",
            "status",
            "joined_at",
        ]
        read_only_fields = ["id", "joined_at", "profile_picture_url", "status"]

    def get_profile_picture_url(self, obj):
        profile = getattr(obj.user, "profile", None)
        if profile and profile.profile_picture:
            return profile.profile_picture.url
        return None

    def get_full_name(self, obj):
        return obj.user.profile.full_name

    def get_role_name(self, obj):
        return obj.role.role.name


class ProjectMembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project memberships (joining projects)"""

    project_id = serializers.PrimaryKeyRelatedField(
        source="project", queryset=Project.objects.all()
    )
    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=ProjectRole.objects.all()
    )

    class Meta:
        model = ProjectMembership
        fields = ["project_id", "role_id"]

    def validate(self, data):
        """Validate the join request"""
        user = self.context["request"].user
        project = data["project"]
        role = data["role"]

        # Check if user is already a member of this project with this role
        if ProjectMembership.objects.filter(
            user=user, project=project, role=role
        ).exists():
            raise serializers.ValidationError(
                "You have already applied for this role in this project."
            )

        # Check if the role belongs to the project
        if role.project != project:
            raise serializers.ValidationError(
                "The specified role does not belong to this project."
            )

        # Check if user is the project owner
        if project.owner == user:
            raise serializers.ValidationError(
                "Project owners cannot join their own projects as members."
            )

        return data

    def create(self, validated_data):
        """Create the membership with the current user"""
        validated_data["user"] = self.context["request"].user
        validated_data["status"] = "pending"
        return super().create(validated_data)


class ProjectMembershipStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating project membership status (approve/reject)"""

    status = serializers.ChoiceField(
        choices=[("approved", "Approved"), ("rejected", "Rejected")],
        help_text="Status to update the membership to",
    )

    class Meta:
        model = ProjectMembership
        fields = ["status"]

    def validate_status(self, value):
        """Validate the status change"""
        membership = self.instance

        # Check if the membership is already in the requested status
        if membership.status == value:
            raise serializers.ValidationError(f"Membership is already {value}.")

        # Only allow changing from 'pending' to 'approved' or 'rejected'
        if membership.status != "pending":
            raise serializers.ValidationError(
                f"Cannot change status from '{membership.status}' to '{value}'."
            )

        return value

    def validate(self, data):
        """Additional validation for the entire serializer"""
        membership = self.instance
        user = self.context["request"].user

        # Only project owners can update membership status
        if membership.project.owner != user:
            raise serializers.ValidationError(
                "Only project owners can update membership status."
            )

        return data


class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for project details including team members"""

    team_members = ProjectMembershipSerializer(
        source="projectmembership_set", many=True, read_only=True
    )

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["team_members"]
