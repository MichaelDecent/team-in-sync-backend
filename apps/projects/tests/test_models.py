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

    def test_project_team_members(self, project, user, another_user, role):
        """Test project team members relationship"""
        designer_role = ProjectRole.objects.create(
            project=project, custom_role_name="Designer", number_required=1
        )

        software_engineer_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )

        ProjectMembership.objects.create(
            project=project, user=user, role=designer_role, status="approved"
        )

        ProjectMembership.objects.create(
            project=project,
            user=another_user,
            role=software_engineer_role,
            status="approved",
        )

        assert project.team_members.count() == 2
        assert user in project.team_members.all()
        assert another_user in project.team_members.all()


@pytest.mark.django_db
class TestProjectRoleModel:
    """Test ProjectRole model"""

    def test_create_project_role_with_predefined_role(self, project, role):
        """Test creating a project role with a predefined role"""
        project_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )

        assert project_role.project == project
        assert project_role.role == role
        assert project_role.custom_role_name is None
        assert project_role.number_required == 1
        assert f"{project.title} - {role.name}" in str(project_role)

    def test_create_project_role_with_custom_name(self, project):
        """Test creating a project role with a custom role name"""
        custom_name = "AI Specialist"
        project_role = ProjectRole.objects.create(
            project=project, custom_role_name=custom_name, number_required=2
        )

        assert project_role.project == project
        assert project_role.role is None
        assert project_role.custom_role_name == custom_name
        assert project_role.number_required == 2
        assert f"{project.title} - {custom_name}" in str(project_role)
        assert project_role.get_role_display == custom_name

    def test_unique_constraint_predefined_role(self, project, role):
        """Test unique constraint on project and predefined role"""
        ProjectRole.objects.create(project=project, role=role, number_required=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRole.objects.create(
                    project=project,
                    role=role,
                    number_required=2,
                )

    def test_unique_constraint_custom_role(self, project):
        """Test unique constraint on project and custom role"""
        custom_name = "Technical Writer"
        ProjectRole.objects.create(
            project=project, custom_role_name=custom_name, number_required=1
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRole.objects.create(
                    project=project,
                    custom_role_name=custom_name,
                    number_required=2,
                )


@pytest.mark.django_db
class TestProjectRoleSkillModel:
    """Test ProjectRoleSkill model"""

    def test_create_project_role_skill_with_predefined_skill(self, project_role, skill):
        """Test creating a project role skill with a predefined skill"""
        role_skill = ProjectRoleSkill.objects.create(
            project_role=project_role, skill=skill
        )

        assert role_skill.project_role == project_role
        assert role_skill.skill == skill
        assert role_skill.custom_skill_name is None
        assert project_role.project.title in str(role_skill)
        assert skill.name in str(role_skill)

    def test_create_project_role_skill_with_custom_name(self, project_role):
        """Test creating a project role skill with a custom skill name"""
        custom_skill = "Quantum Computing"
        role_skill = ProjectRoleSkill.objects.create(
            project_role=project_role, custom_skill_name=custom_skill
        )

        assert role_skill.project_role == project_role
        assert role_skill.skill is None
        assert role_skill.custom_skill_name == custom_skill
        assert project_role.project.title in str(role_skill)
        assert custom_skill in str(role_skill)

    def test_unique_constraint_predefined_skill(self, project_role, skill):
        """Test unique constraint on project_role and predefined skill"""
        ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRoleSkill.objects.create(
                    project_role=project_role,
                    skill=skill,
                )

    def test_unique_constraint_custom_skill(self, project_role):
        """Test unique constraint on project_role and custom skill"""
        custom_skill = "AI Ethics"
        ProjectRoleSkill.objects.create(
            project_role=project_role, custom_skill_name=custom_skill
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectRoleSkill.objects.create(
                    project_role=project_role,
                    custom_skill_name=custom_skill,
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
        designer_role = ProjectRole.objects.create(
            project=project, custom_role_name="Designer", number_required=1
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
        # Third test - should work because different role
        ProjectMembership.objects.create(
            project=project,
            user=user,
            role=software_engineer_role,  # Different role
            status="pending",
        )
