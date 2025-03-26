import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.users.models.profile_models import UserProfile, UserSkill


@pytest.mark.django_db
class TestUserProfileView:
    """Test the UserProfileView."""

    def test_get_profile_authenticated(self, auth_client, profile, verified_user):
        """Test getting profile for authenticated user."""
        url = reverse("users:user_profile")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["id"] == profile.id
        assert response.data["data"]["user"] == verified_user.id

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile for unauthenticated user."""
        url = reverse("users:user_profile")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, auth_client, profile):
        """Test updating profile with valid data."""
        url = reverse("users:user_profile")
        data = {
            "full_name": "John Doe",
            "role": "designer",
            "bio": "I am a designer",
        }

        response = auth_client.patch(url, data, format="multipart")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Profile updated successfully" in response.data["message"]

        # Verify profile was updated
        profile.refresh_from_db()
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.role == "designer"
        assert profile.bio == "I am a designer"

    @pytest.mark.skipif(reason="Skipping image upload tests in CI environment")
    def test_update_profile_with_image(
        self, mock_cloudinary_upload, auth_client, profile, tmpdir
    ):
        """Test updating profile with an image."""
        # Set up mock return value
        mock_cloudinary_upload.return_value = {
            "public_id": "test_id",
            "secure_url": "https://example.com/test.jpg",
        }

        url = reverse("users:user_profile")

        # Create a test image file
        img_path = tmpdir.join("test_image.jpg")
        with open(img_path, "wb") as f:
            f.write(b"test image content")

        with open(img_path, "rb") as img:
            data = {
                "profile_picture": SimpleUploadedFile(
                    name="test_image.jpg", content=img.read(), content_type="image/jpeg"
                )
            }
            response = auth_client.patch(url, data, format="multipart")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify the profile was updated with a Cloudinary URL
        profile.refresh_from_db()
        assert "profile_picture_url" in response.data["data"]

    def test_update_profile_invalid_data(self, auth_client):
        """Test updating profile with invalid data."""
        url = reverse("users:user_profile")
        data = {
            "role": "invalid_role",
        }

        response = auth_client.patch(url, data, format="multipart")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "role" in response.data["errors"]


@pytest.mark.django_db
class TestUserSkillView:
    """Test the UserSkillView."""

    def test_get_all_skills(self, auth_client, skill1, skill2):
        """Test getting all available skills."""
        url = reverse("users:skills")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) == 2

        skill_names = [s["name"] for s in response.data["data"]]
        assert skill_names == sorted(skill_names)

    def test_get_skills_unauthenticated(self, api_client):
        """Test getting skills when unauthenticated."""
        url = reverse("users:user_skills")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_skill_to_profile(self, auth_client, profile, skill1):
        """Test adding a skill to user profile."""
        url = reverse("users:user_skills")
        data = {"skill": skill1.id}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Skill added successfully" in response.data["message"]
        assert "id" in response.data["data"]
        assert response.data["data"]["skill"] == skill1.id

        # Verify skill was added to profile
        assert UserSkill.objects.filter(profile=profile, skill=skill1).exists()

    def test_add_nonexistent_skill(self, auth_client):
        """Test adding a skill that doesn't exist."""
        url = reverse("users:user_skills")
        data = {"skill": 999}  # Non-existent skill ID

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "skill" in response.data["errors"]

    def test_add_duplicate_skill(self, auth_client, profile, user_skill):
        """Test adding a skill that the user already has."""
        url = reverse("users:user_skills")
        data = {"skill": user_skill.skill.id}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "You already have this skill" in str(response.data["errors"])

    def test_remove_skill_from_profile(self, auth_client, profile, user_skill):
        """Test removing a skill from user profile."""
        url = reverse("users:delete_user_skill", kwargs={"skill_id": user_skill.id})

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Skill removed successfully" in response.data["message"]

        # Verify skill was removed
        assert not UserSkill.objects.filter(id=user_skill.id).exists()

    def test_remove_nonexistent_skill(self, auth_client):
        """Test removing a skill that doesn't exist."""
        url = reverse("users:delete_user_skill", kwargs={"skill_id": 999})

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False
        assert "Skill not found" in response.data["message"]

    def test_remove_other_users_skill(self, auth_client, user, skill1):
        """Test removing another user's skill."""
        other_profile = UserProfile.objects.create(user=user)
        other_user_skill = UserSkill.objects.create(profile=other_profile, skill=skill1)

        url = reverse(
            "users:delete_user_skill", kwargs={"skill_id": other_user_skill.id}
        )

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

        # Verify skill was not removed
        assert UserSkill.objects.filter(id=other_user_skill.id).exists()
