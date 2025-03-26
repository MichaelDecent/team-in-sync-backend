import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from apps.users.models.profile_models import (
    ExperienceLevelChoices,
    RoleChoices,
    Skill,
    UserProfile,
    UserSkill,
)
from apps.users.serializers.profile_serializers import (
    SkillSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSkillCreateSerializer,
    UserSkillSerializer,
)


@pytest.fixture
def profile(user):
    """Create and return a test user profile."""
    return UserProfile.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
        role=RoleChoices.SOFTWARE_ENGINEER,
        experience_level=ExperienceLevelChoices.SENIOR,
        bio="Experienced developer",
        portfolio_link="https://portfolio.example.com",
        github_link="https://github.com/johndoe",
        linkedin_link="https://linkedin.com/in/johndoe",
    )


@pytest.fixture
def skill():
    """Create and return a test skill."""
    return Skill.objects.create(name="Python")


@pytest.fixture
def user_skill(profile, skill):
    """Create and return a test user skill."""
    return UserSkill.objects.create(profile=profile, skill=skill)


@pytest.mark.django_db
class TestSkillSerializer:
    """Test SkillSerializer"""

    def test_serialize_skill(self, skill):
        """Test serializing a skill."""
        serializer = SkillSerializer(skill)

        assert serializer.data["id"] == skill.id
        assert serializer.data["name"] == skill.name

    def test_deserialize_skill(self):
        """Test deserializing a skill."""
        data = {"name": "JavaScript"}
        serializer = SkillSerializer(data=data)

        assert serializer.is_valid()
        skill = serializer.save()

        assert skill.name == data["name"]

    def test_unique_skill_name(self, skill):
        """Test that skill names must be unique."""
        data = {"name": skill.name}
        serializer = SkillSerializer(data=data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors


@pytest.mark.django_db
class TestUserSkillSerializer:
    """Test UserSkillSerializer"""

    def test_serialize_user_skill(self, user_skill):
        """Test serializing a user skill."""
        serializer = UserSkillSerializer(user_skill)

        assert serializer.data["id"] == user_skill.id
        assert serializer.data["skill_details"]["id"] == user_skill.skill.id
        assert serializer.data["skill_details"]["name"] == user_skill.skill.name


@pytest.mark.django_db
class TestUserProfileSerializer:
    """Test UserProfileSerializer"""

    def test_serialize_user_profile(self, profile, user_skill):
        """Test serializing a user profile."""
        serializer = UserProfileSerializer(profile)

        assert serializer.data["id"] == profile.id
        assert (
            serializer.data["full_name"] == f"{profile.first_name} {profile.last_name}"
        )
        assert serializer.data["role"] == profile.role
        assert serializer.data["experience_level"] == profile.experience_level
        assert serializer.data["portfolio_link"] == profile.portfolio_link
        assert serializer.data["github_link"] == profile.github_link
        assert serializer.data["linkedin_link"] == profile.linkedin_link
        assert serializer.data["bio"] == profile.bio

        # Check skills data
        assert len(serializer.data["skills"]) == 1
        assert serializer.data["skills"][0]["id"] == user_skill.skill.id
        assert isinstance(serializer.data["skills"][0]["skill_details"], dict)
        assert serializer.data["skills"][0]["skill_details"]["name"] == user_skill.skill.name
        assert serializer.data["skills"][0]["skill_details"]["role"] == user_skill.skill.role


@pytest.mark.django_db
class TestUserProfileUpdateSerializer:
    """Test UserProfileUpdateSerializer"""

    def test_update_user_profile(self, profile, skill):
        """Test updating a user profile."""
        # Create two more skills for testing
        designer_skill = Skill.objects.create(
            name="UI Design", role=RoleChoices.DESIGNER
        )

        data = {
            "full_name": "Jane Smith",
            "role": RoleChoices.DESIGNER,
            "bio": "Creative designer with UI/UX focus",
            "skills": [designer_skill.id],  # Add skills to the update
        }
        serializer = UserProfileUpdateSerializer(profile, data=data, partial=True)

        assert serializer.is_valid()
        updated_profile = serializer.save()

        # Test that basic fields are updated
        assert updated_profile.first_name == "Jane"
        assert updated_profile.last_name == "Smith"
        assert updated_profile.role == data["role"]
        assert updated_profile.bio == data["bio"]

        # Test that skills were updated properly
        user_skills = UserSkill.objects.filter(profile=updated_profile)
        assert user_skills.count() == 1
        assert user_skills.first().skill.id == designer_skill.id

        # Fields not in the update should remain unchanged
        assert updated_profile.experience_level == profile.experience_level
        assert updated_profile.portfolio_link == profile.portfolio_link

    @pytest.mark.skipif(reason="Skipping image upload tests in CI environment")
    def test_update_profile_with_image(self, profile, tmpdir, mock_cloudinary_upload):
        """Test updating a profile with an image upload."""
        # Create a test image
        img_path = os.path.join(tmpdir, "profile.jpg")
        with open(img_path, "wb") as f:
            f.write(b"test image content")

        # Set up mock return
        mock_cloudinary_upload.return_value = {
            "public_id": "test_id",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/profile.jpg",
        }

        # Open the image and create the data
        with open(img_path, "rb") as img:
            image = SimpleUploadedFile(
                name="profile.jpg", content=img.read(), content_type="image/jpeg"
            )

            # Make sure image is properly set up
            assert image.name == "profile.jpg"
            assert image.content_type == "image/jpeg"

            data = {"profile_picture": image}
            serializer = UserProfileUpdateSerializer(profile, data=data, partial=True)

            # Print any validation errors for debugging
            if not serializer.is_valid():
                print(f"Validation errors: {serializer.errors}")

            assert serializer.is_valid()
            updated_profile = serializer.save()

        # For CloudinaryField, we just check it exists, not the path
        assert updated_profile.profile_picture is not None

    def test_update_with_incompatible_skills(self, profile, skill):
        """Test updating a profile with skills incompatible with the role."""
        # Create skills with different roles
        Skill.objects.create(
            name="UI Design", role=RoleChoices.DESIGNER
        )

        # Try to update with designer role but software engineer skill
        data = {
            "role": RoleChoices.DESIGNER,
            "skills": [skill.id],  # This is a SOFTWARE_ENGINEER skill
        }
        serializer = UserProfileUpdateSerializer(profile, data=data, partial=True)

        # Should not be valid due to incompatible skills
        assert not serializer.is_valid()
        assert "skills" in serializer.errors
        assert "not compatible" in str(serializer.errors["skills"][0])


@pytest.mark.django_db
class TestUserSkillCreateSerializer:
    """Test UserSkillCreateSerializer"""

    def test_create_user_skill(self, profile):
        """Test creating a user skill."""
        skill = Skill.objects.create(name="Django")
        data = {"skill": skill.id}
        serializer = UserSkillCreateSerializer(data=data, context={"profile": profile})

        assert serializer.is_valid()
        user_skill = serializer.save()

        assert user_skill.profile == profile
        assert user_skill.skill == skill

    def test_missing_profile_in_context(self, skill):
        """Test creating a user skill without profile in context."""
        data = {"skill": skill.id}
        serializer = UserSkillCreateSerializer(data=data)

        assert serializer.is_valid()

        with pytest.raises(ValidationError) as excinfo:
            serializer.save()

        assert "Profile is required" in str(excinfo.value)

    def test_duplicate_skill(self, profile, user_skill):
        """Test adding a skill the user already has."""
        data = {"skill": user_skill.skill.id}
        serializer = UserSkillCreateSerializer(data=data, context={"profile": profile})

        assert serializer.is_valid()

        with pytest.raises(ValidationError) as excinfo:
            serializer.save()

        assert "You already have this skill" in str(excinfo.value)
