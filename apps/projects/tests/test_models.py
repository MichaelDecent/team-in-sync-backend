import pytest
from django.db import transaction
from django.db.utils import IntegrityError

from apps.projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
)
from apps.users.models.profile_models import Role


@pytest.mark.django_db
class TestProjectModel:
    """Test Project model"""

    def test_create_project(self, user):
        """Test creating a project"""
        project = Project.objects.create(
            title="New Project",
            description="Project description",
            owner=user,
            status="in_progress",
        )

        assert project.title == "New Project"
        assert project.description == "Project description"
        assert project.owner == user
        assert project.status == "in_progress"
        assert str(project) == "New Project"

    def test_project_team_members(self, project, user, role):
        """Test project team members relationship"""

        software_engineer_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )

        ProjectMembership.objects.create(
            project=project,
            user=user,
            role=software_engineer_role,
            status="approved",
        )

        assert project.team_members.count() == 1
        assert user in project.team_members.all()


@pytest.mark.django_db
class TestProjectRoleModel:
    """Test ProjectRole model"""

    def test_create_project_role(self, project):
        """Test creating a project role"""
        # Create a new role for this test
        role = Role.objects.create(name="AI Specialist")
        project_role = ProjectRole.objects.create(
            project=project, role=role, number_required=2
        )

        assert project_role.project == project
        assert project_role.role == role
        assert project_role.number_required == 2
        assert f"{project.title} - {role.name}" in str(project_role)

    def test_unique_constraint(self, project, role):
        """Test unique constraint on project and role"""
        ProjectRole.objects.create(project=project, role=role, number_required=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRole.objects.create(
                    project=project,
                    role=role,
                    number_required=2,
                )


@pytest.mark.django_db
class TestProjectRoleSkillModel:
    """Test ProjectRoleSkill model"""

    def test_create_project_role_skill(self, project_role, skill):
        """Test creating a project role skill"""
        role_skill = ProjectRoleSkill.objects.create(
            project_role=project_role, skill=skill
        )

        assert role_skill.project_role == project_role
        assert role_skill.skill == skill
        assert project_role.project.title in str(role_skill)
        assert skill.name in str(role_skill)

    def test_unique_constraint_skill(self, project_role, skill):
        """Test unique constraint on project_role and skill"""
        ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRoleSkill.objects.create(
                    project_role=project_role,
                    skill=skill,
                )


@pytest.mark.django_db
class TestProjectMembershipModel:
    """Test ProjectMembership model"""

    def test_create_project_membership(self, project, user, role):
        """Test creating a project membership"""
        software_engineer_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )
        membership = ProjectMembership.objects.create(
            project=project, user=user, role=software_engineer_role, status="approved"
        )

        assert membership.project == project
        assert membership.user == user
        assert membership.role == software_engineer_role
        assert membership.status == "approved"
        assert user.email in str(membership)
        assert project.title in str(membership)
        assert "Software Engineer" in str(membership)

    def test_unique_constraint(self, project, user, role):
        """Test unique constraint on user, project and role"""
        designer_role_obj = Role.objects.create(name="Designer")

        designer_role = ProjectRole.objects.create(
            project=project, role=designer_role_obj, number_required=1
        )

        ProjectMembership.objects.create(
            project=project, user=user, role=designer_role, status="approved"
        )

        # Second test - should fail
        with pytest.raises(IntegrityError):
            with transaction.atomic():  # Add transaction context
                ProjectMembership.objects.create(
                    project=project,
                    user=user,
                    role=designer_role,  # Same role, should fail
                    status="pending",
                )

        software_engineer_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )
        ProjectMembership.objects.create(
            project=project,
            user=user,
            role=software_engineer_role,  # Different role
            status="pending",
        )
