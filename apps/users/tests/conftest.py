from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models.profile_models import (
    ExperienceLevelChoices,
    RoleChoices,
    Skill,
    UserProfile,
    UserSkill,
)

from .factories import EmailVerificationTokenFactory, UserFactory, VerifiedUserFactory


@pytest.fixture
def api_client():
    """Return an API client"""
    return APIClient()


@pytest.fixture
def user():
    """Return a user with unverified email"""
    return UserFactory()


@pytest.fixture
def verified_user():
    """Return a user with verified email"""
    return VerifiedUserFactory()


@pytest.fixture
def verification_token(user):
    """Return an email verification token"""
    return EmailVerificationTokenFactory(user=user)


@pytest.fixture
def auth_client(verified_user):
    """Return an authenticated API client"""
    client = APIClient()
    url = reverse("users:login")
    response = client.post(
        url, {"email": verified_user.email, "password": "password123"}, format="json"
    )

    token = response.data["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def profile(verified_user):
    """Return a profile for the verified user"""
    profile, created = UserProfile.objects.get_or_create(
        user=verified_user,
        defaults={
            "first_name": "Test",
            "last_name": "User",
            "role": RoleChoices.DEVELOPER,
            "experience_level": ExperienceLevelChoices.MID_LEVEL,
            "bio": "Test user bio",
        },
    )
    return profile


@pytest.fixture
def empty_profile(user):
    """Return an empty profile for an unverified user"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


@pytest.fixture
def skill1():
    """Return a test skill"""
    skill, created = Skill.objects.get_or_create(name="Python")
    return skill


@pytest.fixture
def skill2():
    """Return another test skill"""
    skill, created = Skill.objects.get_or_create(name="JavaScript")
    return skill


@pytest.fixture
def skill3():
    """Return a third test skill"""
    skill, created = Skill.objects.get_or_create(name="Django")
    return skill


# Update the test files to use skill1 instead of skill
@pytest.fixture
def skill():
    """Alias for skill1 to maintain compatibility"""
    skill, created = Skill.objects.get_or_create(name="Python")
    return skill


@pytest.fixture
def user_skill(profile, skill1):
    """Return a user skill linking a profile and skill"""
    user_skill, created = UserSkill.objects.get_or_create(profile=profile, skill=skill1)
    return user_skill


@pytest.fixture
def mock_cloudinary_upload():
    """Mock Cloudinary upload for testing"""
    with patch("cloudinary.uploader.upload") as mock:
        mock.return_value = {
            "secure_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        }
        yield mock


@pytest.fixture(autouse=True)
def mock_cloudinary():
    """Automatically mock all cloudinary uploads for tests"""
    with patch("cloudinary.uploader.upload_resource", return_value="mocked_public_id"):
        yield
