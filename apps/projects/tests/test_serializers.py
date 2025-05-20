import pytest

from apps.projects.models import ProjectRole
from apps.projects.serializers import (
    ProjectMembershipSerializer,
    ProjectRoleSerializer,
    ProjectRoleSkillSerializer,
    ProjectSerializer,
)


@pytest.mark.django_db
class TestProjectRoleSkillSerializer:
    """Test ProjectRoleSkillSerializer"""

    def test_serialize_project_role_skill_with_predefined_skill(
        self, project_role_skill
    ):
        """Test serializing a project role skill with predefined skill"""
        serializer = ProjectRoleSkillSerializer(project_role_skill)
        data = serializer.data

        assert data["id"] == project_role_skill.id
        assert "skill_name" in data
        assert data["skill_name"] == project_role_skill.skill.name

    def test_validate_either_role_or_name_required(self, role):
        """Test validation that either role or role_input is required"""
        # Test with neither field provided
        serializer = ProjectRoleSerializer(data={"number_required": 1})
        assert not serializer.is_valid()
        assert "role_input is required" in str(serializer.errors)

        # Test with both fields provided
        serializer = ProjectRoleSerializer(
            data={
                "role_input": "Test",
                "number_required": 1,
            }
        )
        assert serializer.is_valid()

    def test_create_with_skill_by_name(self, project_role):
        """Test creating project role skill with skill_input"""
        serializer = ProjectRoleSkillSerializer(data={"skill_input": "GraphQL"})
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        skill = serializer.save(project_role=project_role)
        assert skill.project_role == project_role
        assert skill.skill.name == "GraphQL"


@pytest.mark.django_db
class TestProjectRoleSerializer:
    """Test ProjectRoleSerializer"""

    def test_serialize_project_role_with_predefined_role(
        self, project_role, project_role_skill, role
    ):
        """Test serializing a project role with predefined role"""
        # Update project_role to use the role fixture
        project_role.role = role
        project_role.save()

        serializer = ProjectRoleSerializer(project_role)
        data = serializer.data

        assert data["id"] == project_role.id
        assert "role_name" in data
        assert data["role_name"] == role.name
        # custom_role_name no longer exists
        assert data["number_required"] == project_role.number_required
        assert len(data["required_skills"]) == 1
        assert data["required_skills"][0]["id"] == project_role_skill.id

    def test_create_project_role_with_predefined_role_and_skills(
        self, project, role, skill
    ):
        """Test creating a project role with predefined role and skills_input"""
        data = {
            "role_input": role.name,
            "number_required": 2,
            "skills_input": [skill.name],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role.name == role.name
        assert project_role.number_required == 2
        assert project_role.required_skills.count() == 1
        assert project_role.required_skills.first().skill.name == skill.name

    def test_create_project_role_with_new_role_and_skills(self, project, skill):
        """Test creating a project role with new role name and skills_input"""
        data = {
            "role_input": "DevSecOps Engineer",  # Use role_input
            "number_required": 1,
            "skills_input": [skill.name],  # Use skills_input instead of skill_ids
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role.name == "DevSecOps Engineer"
        assert project_role.number_required == 1
        assert project_role.required_skills.count() == 1
        assert project_role.required_skills.first().skill.name == skill.name

    def test_create_project_role_with_new_role_and_new_skills(self, project):
        """Test creating a project role with both new role and new skills_input"""
        data = {
            "role_input": "AI Researcher",
            "number_required": 2,
            "skills_input": ["Neural Networks", "Reinforcement Learning"],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role.name == "AI Researcher"
        assert project_role.number_required == 2
        assert project_role.required_skills.count() == 2

        skill_names = [skill.skill.name for skill in project_role.required_skills.all()]
        assert "Neural Networks" in skill_names
        assert "Reinforcement Learning" in skill_names

    def test_validate_role_by_name_required(self, role):
        """Test validation that role_input is required"""
        # Test with neither field provided
        serializer = ProjectRoleSerializer(data={"number_required": 1})
        assert not serializer.is_valid()
        assert "role_input is required" in str(serializer.errors)


@pytest.mark.django_db
class TestProjectSerializer:
    """Test ProjectSerializer"""

    # Update ProjectSerializer.create method to handle role_input and skills_input
    def test_create_project_with_mixed_roles_and_skills(self, user, role, skill):
        """Test creating a project with mixed roles/skills"""
        data = {
            "title": "Mixed Roles Project",
            "description": "Project with mixed role types",
            "status": "pending",
            "roles": [
                {
                    "role_input": role.name,
                    "number_required": 2,
                    "skills_input": [skill.name],
                },
                {
                    "role_input": "AR/VR Developer",
                    "number_required": 1,
                    "skills_input": [skill.name],
                },
                {
                    "role_input": "Blockchain Engineer",
                    "number_required": 1,
                    "skills_input": ["Solidity", "Smart Contracts"],
                },
            ],
        }

        serializer = ProjectSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project = serializer.save(owner=user)

        assert project.title == "Mixed Roles Project"
        assert project.description == "Project with mixed role types"
        assert project.status == "pending"
        assert project.owner == user
        assert project.required_roles.count() == 3

        # Check the existing role and its skills_input
        predefined_role = project.required_roles.filter(role__name=role.name).first()
        assert predefined_role is not None
        assert predefined_role.number_required == 2
        assert predefined_role.required_skills.count() == 1
        assert predefined_role.required_skills.first().skill.name == skill.name

        # Check the new role with existing skill
        ar_vr_role = project.required_roles.filter(role__name="AR/VR Developer").first()
        assert ar_vr_role is not None
        assert ar_vr_role.number_required == 1
        assert ar_vr_role.required_skills.count() == 1
        assert ar_vr_role.required_skills.first().skill.name == skill.name

        # Check the new role with new skills_input
        blockchain_role = project.required_roles.filter(
            role__name="Blockchain Engineer"
        ).first()
        assert blockchain_role is not None
        assert blockchain_role.number_required == 1
        assert blockchain_role.required_skills.count() == 2

        skill_names = [
            skill.skill.name for skill in blockchain_role.required_skills.all()
        ]
        assert "Solidity" in skill_names
        assert "Smart Contracts" in skill_names


@pytest.mark.django_db
class TestProjectMembershipSerializer:
    """Test ProjectMembershipSerializer"""

    def test_create_project_membership(self, user, project, role):
        """Test creating a project membership"""
        # First create a project role
        project_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )

        data = {
            "user": user.id,
            "project": project.id,
            "role_id": project_role.id,
            "status": "pending",
        }

        serializer = ProjectMembershipSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        membership = serializer.save()

        assert membership.user == user
        assert membership.project == project
        assert membership.role == project_role
        assert membership.status == "pending"
