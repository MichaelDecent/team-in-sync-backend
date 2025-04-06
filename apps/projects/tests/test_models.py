import pytest
from django.db import transaction
from django.db.utils import IntegrityError

from apps.projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
)


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

    def test_project_team_members(self, project, user, another_user):
        """Test project team members relationship"""
        ProjectMembership.objects.create(
            project=project, user=user, role="designer", status="approved"
        )

        ProjectMembership.objects.create(
            project=project,
            user=another_user,
            role="software_engineer",
            status="approved",
        )

        assert project.team_members.count() == 2
        assert user in project.team_members.all()
        assert another_user in project.team_members.all()


@pytest.mark.django_db
class TestProjectRoleModel:
    """Test ProjectRole model"""

    def test_create_project_role(self, project):
        """Test creating a project role"""
        role = ProjectRole.objects.create(
            project=project, role="designer", number_required=1
        )

        assert role.project == project
        assert role.role == "designer"
        assert role.number_required == 1
        assert "Test Project - Designer" in str(role)

    def test_unique_constraint(self, project):
        """Test unique constraint on project and role"""
        ProjectRole.objects.create(project=project, role="designer", number_required=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRole.objects.create(
                    project=project,
                    role="designer",
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

    def test_unique_constraint(self, project_role, skill):
        """Test unique constraint on project_role and skill"""
        ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        with pytest.raises(IntegrityError):
            with transaction.atomic():  # Add transaction context
                ProjectRoleSkill.objects.create(
                    project_role=project_role,
                    skill=skill,  # Same skill, should fail
                )


@pytest.mark.django_db
class TestProjectMembershipModel:
    """Test ProjectMembership model"""

    def test_create_project_membership(self, project, user):
        """Test creating a project membership"""
        membership = ProjectMembership.objects.create(
            project=project, user=user, role="designer", status="approved"
        )

        assert membership.project == project
        assert membership.user == user
        assert membership.role == "designer"
        assert membership.status == "approved"
        assert user.email in str(membership)
        assert project.title in str(membership)
        assert "Designer" in str(membership)

    def test_unique_constraint(self, project, user):
        """Test unique constraint on user, project and role"""
        # First test
        ProjectMembership.objects.create(
            project=project, user=user, role="designer", status="approved"
        )

        # Second test - should fail
        with pytest.raises(IntegrityError):
            with transaction.atomic():  # Add transaction context
                ProjectMembership.objects.create(
                    project=project,
                    user=user,
                    role="designer",  # Same role, should fail
                    status="pending",
                )

        # Third test - should work because different role
        ProjectMembership.objects.create(
            project=project,
            user=user,
            role="software_engineer",  # Different role
            status="pending",
        )
