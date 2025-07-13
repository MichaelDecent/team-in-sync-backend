from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.projects.models import Project, FavoriteProject
from apps.users.models.profile_models import Role

User = get_user_model()


class FavoriteProjectModelTest(TestCase):
    """Test FavoriteProject model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.role = Role.objects.create(name="Developer")
        self.project = Project.objects.create(
            title="Test Project",
            description="A test project",
            owner=self.user,
            status="in_progress",
        )

    def test_favorite_project_creation(self):
        """Test creating a favorite project"""
        favorite = FavoriteProject.objects.create(user=self.user, project=self.project)
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.project, self.project)
        self.assertIsNotNone(favorite.created_at)

    def test_unique_constraint(self):
        """Test that a user can't favorite the same project twice"""
        FavoriteProject.objects.create(user=self.user, project=self.project)

        with self.assertRaises(Exception):  # Should raise IntegrityError
            FavoriteProject.objects.create(user=self.user, project=self.project)


class FavoriteProjectAPITest(APITestCase):
    """Test FavoriteProject API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.role = Role.objects.create(name="Developer")
        self.project = Project.objects.create(
            title="Test Project",
            description="A test project",
            owner=self.user,
            status="in_progress",
        )
        self.client.force_authenticate(user=self.user)

    def test_add_to_favorites(self):
        """Test adding a project to favorites"""
        url = "/api/v1/projects/favorites/"
        response = self.client.post(url, {"project": self.project.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            FavoriteProject.objects.filter(
                user=self.user, project=self.project
            ).exists()
        )

    def test_remove_from_favorites(self):
        """Test removing a project from favorites"""
        # First add to favorites
        favorite = FavoriteProject.objects.create(user=self.user, project=self.project)

        url = f"/api/v1/projects/favorites/{favorite.id}/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            FavoriteProject.objects.filter(
                user=self.user, project=self.project
            ).exists()
        )

    def test_list_favorites(self):
        """Test listing user's favorite projects"""
        # Add a project to favorites
        FavoriteProject.objects.create(user=self.user, project=self.project)

        url = "/api/v1/projects/favorites/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["project"], self.project.id)

    def test_is_favorited_field(self):
        """Test that is_favorited field is included in project serialization"""
        # Add project to favorites
        FavoriteProject.objects.create(user=self.user, project=self.project)

        url = f"/api/v1/projects/projects/{self.project.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_favorited"])
