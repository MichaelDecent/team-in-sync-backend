import pytest
from django.contrib.auth import get_user_model

from apps.users.models import EmailVerificationToken

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
        )

        assert user.email == "testuser@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.check_password("password123")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active
        assert not user.email_verified

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="password123",
        )

        assert admin.email == "admin@example.com"
        assert admin.first_name == "Admin"
        assert admin.last_name == "User"
        assert admin.check_password("password123")
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active

    def test_user_str_method(self):
        """Test User string representation"""
        user = User.objects.create_user(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
        )

        assert str(user) == "testuser@example.com"


@pytest.mark.django_db
class TestVerificationTokenModel:
    """Test EmailVerificationToken model"""

    def test_token_creation(self):
        """Test creating a verification token"""
        user = User.objects.create_user(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
        )

        token = EmailVerificationToken.objects.create(user=user)

        assert token.user == user
        assert token.token is not None
        assert token.created_at is not None

    def test_token_str_method(self):
        """Test EmailVerificationToken string representation"""
        user = User.objects.create_user(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="password123",
        )

        token = EmailVerificationToken.objects.create(user=user)

        assert str(token) == f"testuser@example.com - {token.token}"
