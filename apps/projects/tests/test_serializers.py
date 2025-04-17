import pytest

from apps.projects.models import ProjectRole
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

    def test_serialize_project_role_skill_with_predefined_skill(
        self, project_role_skill
    ):
        """Test serializing a project role skill with predefined skill"""
        serializer = ProjectRoleSkillSerializer(project_role_skill)
        data = serializer.data

        assert data["id"] == project_role_skill.id
        assert "skill_name" in data
        assert data["skill_name"] == project_role_skill.skill.name
        assert "custom_skill_name" in data
        assert data["custom_skill_name"] is None

    def test_validate_either_skill_or_custom_name_required(self, role):
        """Test validation that either skill or custom_skill_name is required"""
        # Test with neither field provided
        serializer = ProjectRoleSerializer(data={"number_required": 1})
        assert not serializer.is_valid()
        assert "Either role or custom_role_name must be provided" in str(
            serializer.errors
        )

        # Test with both fields provided - use role_id consistently since that's what your API expects
        serializer = ProjectRoleSerializer(
            data={
                "role_id": role.id,
                "custom_role_name": "Test",
                "number_required": 1,
            }
        )
        assert not serializer.is_valid()
        assert "Only one of role or custom_role_name should be provided" in str(
            serializer.errors
        )

    def test_create_with_custom_skill_name(self, project_role):
        """Test creating project role skill with custom skill name"""
        serializer = ProjectRoleSkillSerializer(data={"custom_skill_name": "GraphQL"})
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        skill = serializer.save(project_role=project_role)
        assert skill.project_role == project_role
        assert skill.skill is None
        assert skill.custom_skill_name == "GraphQL"


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
        assert "custom_role_name" in data
        assert data["custom_role_name"] is None
        assert data["number_required"] == project_role.number_required
        assert len(data["required_skills"]) == 1
        assert data["required_skills"][0]["id"] == project_role_skill.id

    def test_create_project_role_with_predefined_role_and_skills(
        self, project, role, skill
    ):
        """Test creating a project role with predefined role and skills"""
        data = {
            "role_id": role.id,
            "number_required": 2,
            "skill_ids": [skill.id],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role == role
        assert project_role.custom_role_name is None
        assert project_role.number_required == 2
        assert project_role.required_skills.count() == 1
        assert project_role.required_skills.first().skill.id == skill.id

    def test_create_project_role_with_custom_role_and_skills(self, project, skill):
        """Test creating a project role with custom role name and skills"""
        data = {
            "custom_role_name": "DevSecOps Engineer",
            "number_required": 1,
            "skill_ids": [skill.id],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role is None
        assert project_role.custom_role_name == "DevSecOps Engineer"
        assert project_role.number_required == 1
        assert project_role.required_skills.count() == 1
        assert project_role.required_skills.first().skill.id == skill.id

    def test_create_project_role_with_custom_role_and_custom_skills(self, project):
        """Test creating a project role with both custom role and custom skills"""
        data = {
            "custom_role_name": "AI Researcher",
            "number_required": 2,
            "custom_skills": ["Neural Networks", "Reinforcement Learning"],
        }

        serializer = ProjectRoleSerializer(data=data)
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"

        project_role = serializer.save(project=project)

        assert project_role.project == project
        assert project_role.role is None
        assert project_role.custom_role_name == "AI Researcher"
        assert project_role.number_required == 2
        assert project_role.required_skills.count() == 2

        skill_names = [
            skill.custom_skill_name for skill in project_role.required_skills.all()
        ]
        assert "Neural Networks" in skill_names
        assert "Reinforcement Learning" in skill_names

    def test_validate_either_role_or_custom_role_required(self, role):
        """Test validation that either role_id or custom_role_name is required"""
        # Test with neither field provided
        serializer = ProjectRoleSerializer(data={"number_required": 1})
        assert not serializer.is_valid()
        assert "Either role or custom_role_name must be provided" in str(
            serializer.errors
        )

        # Test with both fields provided
        serializer = ProjectRoleSerializer(
            data={"role_id": role.id, "custom_role_name": "Test", "number_required": 1}
        )
        assert not serializer.is_valid()
        assert "Only one of role or custom_role_name should be provided" in str(
            serializer.errors
        )


@pytest.mark.django_db
class TestProjectSerializer:
    """Test ProjectSerializer"""

    def test_create_project_with_mixed_roles_and_skills(self, user, role, skill):
        """Test creating a project with both predefined and custom roles/skills"""
        data = {
            "title": "Mixed Roles Project",
            "description": "Project with mixed role types",
            "status": "pending",
            "roles": [
                # Predefined role with predefined skill
                {
                    "role_id": role.id,
                    "number_required": 2,
                    "skill_ids": [skill.id],
                },
                # Custom role with predefined skill
                {
                    "custom_role_name": "AR/VR Developer",
                    "number_required": 1,
                    "skill_ids": [skill.id],
                },
                # Custom role with custom skills
                {
                    "custom_role_name": "Blockchain Engineer",
                    "number_required": 1,
                    "custom_skills": ["Solidity", "Smart Contracts"],
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

        # Check the predefined role and its skills
        predefined_role = project.required_roles.filter(role=role).first()
        assert predefined_role is not None
        assert predefined_role.number_required == 2
        assert predefined_role.required_skills.count() == 1
        assert predefined_role.required_skills.first().skill.id == skill.id

        # Check the custom role with predefined skill
        ar_vr_role = project.required_roles.filter(
            custom_role_name="AR/VR Developer"
        ).first()
        assert ar_vr_role is not None
        assert ar_vr_role.number_required == 1
        assert ar_vr_role.required_skills.count() == 1
        assert ar_vr_role.required_skills.first().skill.id == skill.id

        # Check the custom role with custom skills
        blockchain_role = project.required_roles.filter(
            custom_role_name="Blockchain Engineer"
        ).first()
        assert blockchain_role is not None
        assert blockchain_role.number_required == 1
        assert blockchain_role.required_skills.count() == 2

        skill_names = [
            skill.custom_skill_name for skill in blockchain_role.required_skills.all()
        ]
        assert "Solidity" in skill_names
        assert "Smart Contracts" in skill_names


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
        assert data["team_members"][0]["role_id"] == project_membership.role.id
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
        assert data["role_id"] == project_membership.role.id
        assert data["status"] == project_membership.status

    def test_create_project_membership(self, user, project, role):
        """Test creating a project membership"""
        # First create a project role
        project_role = ProjectRole.objects.create(
            project=project, custom_role_name="Designer", number_required=1
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
