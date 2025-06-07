from rest_framework import serializers

from apps.users.models.profile_models import Role, Skill

from .models import Project, ProjectMembership, ProjectRole, ProjectRoleSkill


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
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]

    def create(self, validated_data):
        roles_data = validated_data.pop("roles", [])
        project = Project.objects.create(**validated_data)

        for role_data in roles_data:
            skill_names = role_data.pop("skills_input", [])
            role_name = role_data.pop("role_input", None)

            # Process role by name
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                role_data["role"] = role

            project_role = ProjectRole.objects.create(project=project, **role_data)

            # Add skills by name
            for skill_name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        return project


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for project membership"""

    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=ProjectRole.objects.all()
    )
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMembership
        fields = [
            "id",
            "user",
            "project",
            "profile_picture_url",
            "role_id",
            "status",
            "joined_at",
        ]
        read_only_fields = ["id", "joined_at", "profile_picture_url", "status"]

    def get_profile_picture_url(self, obj):
        """Get the URL of the profile picture if it exists"""
        if obj.user.profile.profile_picture:
            return obj.user.profile.profile_picture.url
        return None


class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for project details including team members"""

    team_members = ProjectMembershipSerializer(
        source="projectmembership_set", many=True, read_only=True
    )

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["team_members"]
