from rest_framework import serializers

from apps.users.models.profile_models import Role, Skill

from .models import Project, ProjectMembership, ProjectRole, ProjectRoleSkill


class ProjectRoleSkillSerializer(serializers.ModelSerializer):
    """Serializer for project role skill"""

    skill_name = serializers.CharField(source="skill.name", read_only=True)
    skill = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), required=False, allow_null=True, write_only=True
    )
    custom_skill_name = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = ProjectRoleSkill
        fields = ["id", "skill", "skill_name", "custom_skill_name"]

    def validate(self, data):
        """Ensure either skill or custom_skill_name is provided, but not both."""
        skill = data.get("skill")
        custom_skill_name = data.get("custom_skill_name")

        if skill is None and not custom_skill_name:
            raise serializers.ValidationError(
                "Either skill or custom_skill_name must be provided."
            )
        if skill and custom_skill_name:
            raise serializers.ValidationError(
                "Only one of skill or custom_skill_name should be provided."
            )

        return data


class ProjectRoleSerializer(serializers.ModelSerializer):
    """Serializer for project role with its required skills"""

    required_skills = ProjectRoleSkillSerializer(many=True, read_only=True)
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )
    custom_skills = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False, default=list
    )
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        source="role",
    )
    custom_role_name = serializers.CharField(required=False, allow_null=True)
    role_name = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ProjectRole
        fields = [
            "id",
            "role_id",
            "custom_role_name",
            "role_name",
            "number_required",
            "required_skills",
            "skill_ids",
            "custom_skills",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """Ensure either role or custom_role_name is provided, but not both."""
        role = data.get("role")
        custom_role_name = data.get("custom_role_name")

        if role is None and not custom_role_name:
            raise serializers.ValidationError(
                "Either role or custom_role_name must be provided."
            )
        if role and custom_role_name:
            raise serializers.ValidationError(
                "Only one of role or custom_role_name should be provided."
            )

        return data

    def create(self, validated_data):
        skill_ids = validated_data.pop("skill_ids", [])
        custom_skills = validated_data.pop("custom_skills", [])
        project_role = ProjectRole.objects.create(**validated_data)

        for skill_id in skill_ids:
            ProjectRoleSkill.objects.create(
                project_role=project_role, skill_id=skill_id
            )

        for custom_skill in custom_skills:
            ProjectRoleSkill.objects.create(
                project_role=project_role, custom_skill_name=custom_skill
            )

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
            skill_ids = role_data.pop("skill_ids", [])
            custom_skills = role_data.pop("custom_skills", [])
            project_role = ProjectRole.objects.create(project=project, **role_data)

            for skill_id in skill_ids:
                ProjectRoleSkill.objects.create(
                    project_role=project_role, skill_id=skill_id
                )

            for custom_skill in custom_skills:
                ProjectRoleSkill.objects.create(
                    project_role=project_role, custom_skill_name=custom_skill
                )

        return project


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for project membership"""

    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=ProjectRole.objects.all()
    )

    class Meta:
        model = ProjectMembership
        fields = ["id", "user", "project", "role_id", "status", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for project details including team members"""

    team_members = ProjectMembershipSerializer(
        source="projectmembership_set", many=True, read_only=True
    )

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["team_members"]
