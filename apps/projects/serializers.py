from rest_framework import serializers

from .models import Project, ProjectMembership, ProjectRole, ProjectRoleSkill


class ProjectRoleSkillSerializer(serializers.ModelSerializer):
    """Serializer for project role skill"""

    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = ProjectRoleSkill
        fields = ["id", "skill", "skill_name"]


class ProjectRoleSerializer(serializers.ModelSerializer):
    """Serializer for project role with its required skills"""

    required_skills = ProjectRoleSkillSerializer(many=True, read_only=True)
    skill_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = ProjectRole
        fields = ["id", "role", "number_required", "required_skills", "skill_ids"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        skill_ids = validated_data.pop("skill_ids", [])
        project_role = ProjectRole.objects.create(**validated_data)

        # Create project role skills
        for skill_id in skill_ids:
            ProjectRoleSkill.objects.create(
                project_role=project_role, skill_id=skill_id
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

        # Create project roles with their skills
        for role_data in roles_data:
            skill_ids = role_data.pop("skill_ids", [])
            project_role = ProjectRole.objects.create(project=project, **role_data)

            # Create project role skills
            for skill_id in skill_ids:
                ProjectRoleSkill.objects.create(
                    project_role=project_role, skill_id=skill_id
                )

        return project


class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for project membership"""

    class Meta:
        model = ProjectMembership
        fields = ["id", "user", "project", "role", "status", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class ProjectDetailSerializer(ProjectSerializer):
    """Extended serializer for project details including team members"""

    team_members = ProjectMembershipSerializer(
        source="projectmembership_set", many=True, read_only=True
    )

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["team_members"]
