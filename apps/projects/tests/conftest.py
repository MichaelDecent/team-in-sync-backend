import pytest
from rest_framework.test import APIClient

from apps.projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
)
from apps.users.models.profile_models import Role, Skill
from apps.users.tests.factories import VerifiedUserFactory


@pytest.fixture
def api_client():
    """Return an API client"""
    return APIClient()


@pytest.fixture
def user():
    """Return a verified user"""
    return VerifiedUserFactory()


@pytest.fixture
def another_user():
    """Return another verified user"""
    return VerifiedUserFactory()


@pytest.fixture
def auth_client(user):
    """Return an authenticated API client"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def project(user):
    """Return a project"""
    return Project.objects.create(
        title="Test Project",
        description="A test project description",
        owner=user,
        status="pending",
    )


@pytest.fixture
def project_role(project, role):
    """Return a project role"""
    return ProjectRole.objects.create(project=project, role=role, number_required=2)


@pytest.fixture
def role():
    """Return a role for testing"""
    role, _ = Role.objects.get_or_create(name="Software Engineer")
    return role


@pytest.fixture
def skill(role):
    """Return a skill for testing"""
    skill, _ = Skill.objects.get_or_create(
        name="Python",
        defaults={"role": role},
    )
    return skill


@pytest.fixture
def project_role_skill(project_role, skill):
    """Return a project role skill"""
    return ProjectRoleSkill.objects.create(project_role=project_role, skill=skill)


@pytest.fixture
def project_membership(project, another_user, project_role):
    """Return a project membership"""
    return ProjectMembership.objects.create(
        project=project, user=another_user, role=project_role, status="pending"
    )


@pytest.fixture
def custom_role_project(project):
    """Return a project with a custom role"""
    project_role = ProjectRole.objects.create(
        project=project, custom_role_name="Machine Learning Engineer", number_required=1
    )
    return project, project_role


@pytest.fixture
def custom_skill_project_role_skill(project_role):
    """Return a project role skill with custom skill name"""
    return ProjectRoleSkill.objects.create(
        project_role=project_role, custom_skill_name="Natural Language Processing"
    )
