import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectMembership, ProjectRole


@pytest.mark.django_db
class TestProjectViewSet:
    """Test ProjectViewSet"""

    def test_list_projects(self, auth_client, project):
        """Test listing projects"""
        url = reverse("projects:projects-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(p["id"] == project.id for p in response.data)

    def test_retrieve_project(self, auth_client, project):
        """Test retrieving a specific project"""
        url = reverse("projects:projects-detail", kwargs={"pk": project.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == project.id
        assert response.data["title"] == project.title
        assert "team_members" in response.data

    def test_create_project(self, auth_client, user, skill):
        """Test creating a project with roles and skills"""
        url = reverse("projects:projects-list")
        data = {
            "title": "New Project",
            "description": "Project description",
            "status": "pending",
            "roles": [
                {
                    "role": "software_engineer",
                    "number_required": 2,
                    "skill_ids": [skill.id],
                }
            ],
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert response.data["description"] == data["description"]
        assert response.data["status"] == data["status"]
        assert response.data["owner"] == user.id

        # Check if project was created in database
        project = Project.objects.get(id=response.data["id"])
        assert project.title == data["title"]

        # Check if role was created
        role = ProjectRole.objects.filter(project=project).first()
        assert role is not None
        assert role.role == "software_engineer"

        # Check if skill was added to role
        assert role.required_skills.count() == 1
        assert role.required_skills.first().skill_id == skill.id

    def test_update_project(self, auth_client, project):
        """Test updating a project"""
        url = reverse("projects:projects-detail", kwargs={"pk": project.id})
        data = {"title": "Updated Project", "status": "in_progress"}

        response = auth_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == data["title"]
        assert response.data["status"] == data["status"]

        # Check if updates were saved to database
        project.refresh_from_db()
        assert project.title == data["title"]
        assert project.status == data["status"]

    def test_delete_project(self, auth_client, project):
        """Test deleting a project"""
        url = reverse("projects:projects-detail", kwargs={"pk": project.id})

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=project.id).exists()

    def test_unauthorized_project_update(self, api_client, project):
        """Test unauthorized project update"""
        url = reverse("projects:projects-detail", kwargs={"pk": project.id})
        data = {
            "title": "Unauthorized Update",
        }

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_other_user_cannot_update_project(self, project, another_user):
        """Test that another user cannot update someone else's project"""
        client = APIClient()  # Now properly imported
        client.force_authenticate(user=another_user)

        url = reverse("projects:projects-detail", kwargs={"pk": project.id})
        data = {
            "title": "Unauthorized Update",
        }

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


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

    def test_create_membership(self, auth_client, user, project):
        """Test creating a project membership"""
        url = reverse("projects:memberships-list")
        data = {
            "user": user.id,
            "project": project.id,
            "role": "designer",
            "status": "pending",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == data["user"]
        assert response.data["project"] == data["project"]
        assert response.data["role"] == data["role"]
        assert response.data["status"] == data["status"]

        # Check if membership was created in database
        membership = ProjectMembership.objects.get(id=response.data["id"])
        assert membership.user_id == data["user"]
        assert membership.project_id == data["project"]

    def test_my_memberships(self, auth_client, user, project):
        """Test getting current user's memberships"""
        # Create a membership for the authenticated user
        membership = ProjectMembership.objects.create(
            user=user, project=project, role="designer", status="approved"
        )

        url = reverse("projects:memberships-my-memberships")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == membership.id
        assert response.data[0]["user"] == user.id
