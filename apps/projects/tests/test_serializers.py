import pytest

from apps.projects.serializers import (
    ProjectDetailSerializer,
    ProjectMembershipSerializer,
    ProjectRoleSerializer,
    ProjectRoleSkillSerializer,
    ProjectSerializer,
)


@pytest.mark.django_db
class TestProjectRoleSkillSerializer:
    """Test ProjectRoleSkillSerializer"""

    def test_serialize_project_role_skill(self, project_role_skill):
        """Test serializing a project role skill"""
        serializer = ProjectRoleSkillSerializer(project_role_skill)
        data = serializer.data

        assert data["id"] == project_role_skill.id
        assert data["skill"] == project_role_skill.skill.id


@pytest.mark.django_db
class TestProjectRoleSerializer:
    """Test ProjectRoleSerializer"""

    def test_serialize_project_role(self, project_role, project_role_skill):
        """Test serializing a project role"""
        serializer = ProjectRoleSerializer(project_role)
        data = serializer.data

        assert data["id"] == project_role.id
        assert data["role"] == project_role.role
        assert data["number_required"] == project_role.number_required
        assert len(data["required_skills"]) == 1
        assert data["required_skills"][0]["id"] == project_role_skill.id

    def test_create_project_role_with_skills(self, project, skill):
        """Test creating a project role with skills"""
        data = {
            "project": project.id,
            "role": "designer",
            "number_required": 2,
            "skill_ids": [skill.id],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role == "designer"
        assert project_role.number_required == 2
        assert project_role.required_skills.count() == 1
        assert project_role.required_skills.first().skill.id == skill.id


@pytest.mark.django_db
class TestProjectSerializer:
    """Test ProjectSerializer"""

    def test_serialize_project(self, project, project_role):
        """Test serializing a project"""
        serializer = ProjectSerializer(project)
        data = serializer.data

        assert data["id"] == project.id
        assert data["title"] == project.title
        assert data["description"] == project.description
        assert data["status"] == project.status
        assert data["owner"] == project.owner.id
        assert len(data["required_roles"]) == 1
        assert data["required_roles"][0]["id"] == project_role.id

    def test_create_project_with_roles_and_skills(self, user, skill):
        """Test creating a project with roles and skills"""
        data = {
            "title": "New Project",
            "description": "Project description",
            "status": "pending",
            "roles": [
                {
                    "role": "software_engineer",
                    "number_required": 2,
                    "skill_ids": [skill.id],
                },
                {"role": "designer", "number_required": 1, "skill_ids": []},
            ],
        }

        serializer = ProjectSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project = serializer.save(owner=user)

        assert project.title == "New Project"
        assert project.description == "Project description"
        assert project.status == "pending"
        assert project.owner == user
        assert project.required_roles.count() == 2

        # Check the first role and its skills
        software_role = project.required_roles.filter(role="software_engineer").first()
        assert software_role is not None
        assert software_role.number_required == 2
        assert software_role.required_skills.count() == 1
        assert software_role.required_skills.first().skill.id == skill.id

        # Check the second role
        designer_role = project.required_roles.filter(role="designer").first()
        assert designer_role is not None
        assert designer_role.number_required == 1
        assert designer_role.required_skills.count() == 0


@pytest.mark.django_db
class TestProjectDetailSerializer:
    """Test ProjectDetailSerializer"""

    def test_serialize_project_with_members(self, project, project_membership):
        """Test serializing a project with team members"""
        serializer = ProjectDetailSerializer(project)
        data = serializer.data

        assert data["id"] == project.id
        assert data["title"] == project.title
        assert len(data["team_members"]) == 1
        assert data["team_members"][0]["id"] == project_membership.id
        assert data["team_members"][0]["user"] == project_membership.user.id
        assert data["team_members"][0]["role"] == project_membership.role
        assert data["team_members"][0]["status"] == project_membership.status


@pytest.mark.django_db
class TestProjectMembershipSerializer:
    """Test ProjectMembershipSerializer"""

    def test_serialize_project_membership(self, project_membership):
        """Test serializing a project membership"""
        serializer = ProjectMembershipSerializer(project_membership)
        data = serializer.data

        assert data["id"] == project_membership.id
        assert data["user"] == project_membership.user.id
        assert data["project"] == project_membership.project.id
        assert data["role"] == project_membership.role
        assert data["status"] == project_membership.status

    def test_create_project_membership(self, user, project):
        """Test creating a project membership"""
        data = {
            "user": user.id,
            "project": project.id,
            "role": "designer",
            "status": "pending",
        }

        serializer = ProjectMembershipSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        membership = serializer.save()

        assert membership.user == user
        assert membership.project == project
        assert membership.role == "designer"
        assert membership.status == "pending"
