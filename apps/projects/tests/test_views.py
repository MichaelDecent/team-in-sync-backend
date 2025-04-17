import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project, ProjectMembership, ProjectRole


@pytest.mark.django_db
class TestProjectViewSet:
    """Test ProjectViewSet"""

    def test_create_project_with_predefined_and_custom_roles(
        self, auth_client, user, role, skill
    ):
        """Test creating a project with both predefined and custom roles/skills"""
        url = reverse("projects:projects-list")
        data = {
            "title": "Mixed Project",
            "description": "Project with mixed role types",
            "status": "pending",
            "roles": [
                # Predefined role with predefined skill
                {
                    "role_id": role.id,
                    "number_required": 2,
                    "skill_ids": [skill.id],
                },
                # Custom role with custom skills
                {
                    "custom_role_name": "Data Scientist",
                    "number_required": 1,
                    "custom_skills": ["TensorFlow", "PyTorch"],
                },
            ],
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert response.data["description"] == data["description"]

        # Check if project was created in database
        project = Project.objects.get(id=response.data["id"])
        assert project.title == data["title"]

        # Check if roles were created
        assert project.required_roles.count() == 2

        # Check predefined role
        predefined_role = project.required_roles.filter(role=role).first()
        assert predefined_role is not None
        assert predefined_role.number_required == 2
        assert predefined_role.required_skills.count() == 1
        assert predefined_role.required_skills.first().skill_id == skill.id

        # Check custom role
        custom_role = project.required_roles.filter(
            custom_role_name="Data Scientist"
        ).first()
        assert custom_role is not None
        assert custom_role.number_required == 1
        assert custom_role.required_skills.count() == 2

        # Check custom skills
        skill_names = [
            skill.custom_skill_name for skill in custom_role.required_skills.all()
        ]
        assert "TensorFlow" in skill_names
        assert "PyTorch" in skill_names


@pytest.mark.django_db
class TestProjectMembershipViewSet:
    """Test ProjectMembershipViewSet"""

    def test_list_memberships(self, auth_client, project_membership):
        """Test listing project memberships"""
        url = reverse("projects:memberships-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(m["id"] == project_membership.id for m in response.data)

    def test_filter_by_project(self, auth_client, project, project_membership):
        """Test filtering memberships by project"""
        url = f"{reverse('projects:memberships-list')}?project={project.id}"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == project_membership.id

    def test_filter_by_status(self, auth_client, project_membership):
        """Test filtering memberships by status"""
        url = (
            f"{reverse('projects:memberships-list')}?status={project_membership.status}"
        )
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]["status"] == project_membership.status

    def test_create_membership(self, auth_client, user, project, role):
        """Test creating a project membership"""
        project_role = ProjectRole.objects.create(
            project=project, role=role, number_required=1
        )
        url = reverse("projects:memberships-list")
        data = {
            "user": user.id,
            "project": project.id,
            "role_id": project_role.id,
            "status": "pending",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == data["user"]
        assert response.data["project"] == data["project"]
        assert response.data["role_id"] == data["role_id"]
        assert response.data["status"] == data["status"]

        # Check if membership was created in database
        membership = ProjectMembership.objects.get(id=response.data["id"])
        assert membership.user_id == data["user"]
        assert membership.project_id == data["project"]
