import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from apps.users.models.profile_models import (
    ExperienceLevelChoices,
    RoleChoices,
    Skill,
    UserProfile,
    UserSkill,
)


@pytest.mark.django_db
class TestUserProfileModel:
    """Test the UserProfile model."""

    def test_create_user_profile(self, user):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(
            user=user,
            first_name="John",
            last_name="Doe",
            role=RoleChoices.SOFTWARE_ENGINEER,
            experience_level=ExperienceLevelChoices.SENIOR,
            bio="Experienced software developer",
            portfolio_link="https://portfolio.example.com",
            github_link="https://github.com/johndoe",
            linkedin_link="https://linkedin.com/in/johndoe",
        )

        assert profile.user == user
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.role == RoleChoices.SOFTWARE_ENGINEER
        assert profile.experience_level == ExperienceLevelChoices.SENIOR
        assert profile.bio == "Experienced software developer"
        assert profile.portfolio_link == "https://portfolio.example.com"
        assert profile.github_link == "https://github.com/johndoe"
        assert profile.linkedin_link == "https://linkedin.com/in/johndoe"

    def test_profile_str_representation(self, user):
        """Test the string representation of a user profile."""
        profile = UserProfile.objects.create(user=user)
        assert str(profile) == f"Profile for {user.email}"

    def test_full_name_with_first_and_last_name(self, user):
        """Test the full_name property with both first and last name."""
        profile = UserProfile.objects.create(
            user=user, first_name="John", last_name="Doe"
        )
        assert profile.full_name == "John Doe"

    def test_full_name_with_only_first_name(self, user):
        """Test the full_name property with only first name."""
        profile = UserProfile.objects.create(user=user, first_name="John")
        assert profile.full_name == "John"

    def test_full_name_with_only_last_name(self, user):
        """Test the full_name property with only last name."""
        profile = UserProfile.objects.create(user=user, last_name="Doe")
        assert profile.full_name == "Doe"

    def test_full_name_without_names(self, user):
        """Test the full_name property without any names."""
        profile = UserProfile.objects.create(user=user)
        assert profile.full_name == user.email

    def test_profile_picture_upload(self, user, tmpdir, mock_cloudinary_upload):
        """Test uploading a profile picture."""
        # Create a test image
        img_path = os.path.join(tmpdir, "test_image.jpg")
        with open(img_path, "wb") as f:
            f.write(b"test image content")

        # Mock cloudinary upload is already set up in conftest.py
        mock_cloudinary_upload.return_value = {
            "public_id": "test_id",
            "secure_url": "https://res.cloudinary.com/demo/image/upload/test_image.jpg",
        }

        # Create profile with image
        with open(img_path, "rb") as img:
            profile = UserProfile.objects.create(
                user=user,
                profile_picture=SimpleUploadedFile(
                    "test_image.jpg", img.read(), content_type="image/jpeg"
                ),
            )

        assert profile.profile_picture is not None

    def test_one_profile_per_user(self, user):
        """Test that a user can only have one profile."""
        UserProfile.objects.create(user=user)

        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user)


@pytest.mark.django_db
class TestSkillModel:
    """Test the Skill model."""

    def test_create_skill(self):
        """Test creating a skill."""
        skill = Skill.objects.create(name="Python")

        assert skill.name == "Python"
        assert skill.role == RoleChoices.SOFTWARE_ENGINEER
        assert str(skill) == "Python (Software Engineer)"

    def test_skill_uniqueness(self):
        """Test that skill names are unique."""
        Skill.objects.create(name="Django")

        with pytest.raises(IntegrityError):
            Skill.objects.create(name="Django")


@pytest.mark.django_db
class TestUserSkillModel:
    """Test the UserSkill model."""

    def test_add_skill_to_profile(self, user):
        """Test adding a skill to a user profile."""
        profile = UserProfile.objects.create(user=user)
        skill = Skill.objects.create(name="JavaScript")

        user_skill = UserSkill.objects.create(profile=profile, skill=skill)

        assert user_skill.profile == profile
        assert user_skill.skill == skill
        assert str(user_skill) == f"{user.email} - JavaScript"

    def test_skills_relationship(self, user):
        """Test the relationship between user profiles and skills."""
        profile = UserProfile.objects.create(user=user)
        skill1 = Skill.objects.create(name="Python")
        skill2 = Skill.objects.create(name="JavaScript")

        UserSkill.objects.create(profile=profile, skill=skill1)
        UserSkill.objects.create(profile=profile, skill=skill2)

        # Test accessing skills through profile
        assert profile.skills.count() == 2
        assert set(profile.skills.values_list("skill__name", flat=True)) == {
            "Python",
            "JavaScript",
        }

    def test_unique_user_skill_constraint(self, user):
        """Test that a user can't have the same skill twice."""
        profile = UserProfile.objects.create(user=user)
        skill = Skill.objects.create(name="React")

        UserSkill.objects.create(profile=profile, skill=skill)

        with pytest.raises(IntegrityError):
            UserSkill.objects.create(profile=profile, skill=skill)

    def test_delete_skill_cascades(self, user):
        """Test that deleting a skill cascades to UserSkill records."""
        profile = UserProfile.objects.create(user=user)
        skill = Skill.objects.create(name="TypeScript")

        user_skill = UserSkill.objects.create(profile=profile, skill=skill)
        skill.delete()

        assert UserSkill.objects.filter(id=user_skill.id).count() == 0

    def test_delete_profile_cascades(self, user):
        """Test that deleting a profile cascades to UserSkill records."""
        profile = UserProfile.objects.create(user=user)
        skill = Skill.objects.create(name="Vue")

        user_skill = UserSkill.objects.create(profile=profile, skill=skill)
        profile.delete()

        assert UserSkill.objects.filter(id=user_skill.id).count() == 0


@pytest.mark.django_db
class TestRoleAndExperienceChoices:
    """Test the role and experience level choices."""

    def test_role_choices(self, user):
        """Test setting and retrieving role choices."""
        profile = UserProfile.objects.create(user=user, role=RoleChoices.DESIGNER)
        assert profile.role == RoleChoices.DESIGNER
        assert profile.get_role_display() == "Designer"

    def test_experience_level_choices(self, user):
        """Test setting and retrieving experience level choices."""
        profile = UserProfile.objects.create(
            user=user, experience_level=ExperienceLevelChoices.SENIOR
        )
        assert profile.experience_level == ExperienceLevelChoices.SENIOR
        assert profile.get_experience_level_display() == "Senior (5-8 years)"
