import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from apps.users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestRegisterSerializer:
    """Test RegisterSerializer"""

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            "email": "newuser@example.com",
            "password": "StrongP@ssw0rd123",
        }

        serializer = RegisterSerializer(data=data)

        assert serializer.is_valid()
        user = serializer.save()
        assert user.email == data["email"]
        assert user.check_password(data["password"])

    def test_missing_fields(self):
        """Test serializer with missing required fields"""
        data = {
            "email": "newuser@example.com",
        }

        serializer = RegisterSerializer(data=data)

        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_duplicate_email(self, user):
        """Test serializer with duplicate email"""
        data = {
            "email": user.email,
            "password": "password123",
        }

        serializer = RegisterSerializer(data=data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """Test LoginSerializer"""

    def test_valid_credentials(self, verified_user, rf):
        """Test serializer with valid credentials"""
        request = rf.post("/fake-url/")

        data = {
            "email": verified_user.email,
            "password": "password123",
        }

        serializer = LoginSerializer(data=data, context={"request": request})

        assert serializer.is_valid()
        assert serializer.validated_data["user"] == verified_user

    def test_invalid_credentials(self, verified_user, rf):
        """Test serializer with invalid credentials"""
        request = rf.post("/fake-url/")

        data = {
            "email": verified_user.email,
            "password": "wrongpassword",
        }

        serializer = LoginSerializer(data=data, context={"request": request})

        # Fix: Instead of checking validation, wrap in try/except to catch the exception
        try:
            serializer.is_valid()
            assert False, "Should have raised AuthenticationFailed"
        except AuthenticationFailed as e:
            assert "Invalid credentials" in str(e)


@pytest.mark.django_db
class TestUserSerializer:
    """Test UserSerializer"""

    def test_serialization(self, verified_user):
        """Test serializing a user instance"""
        serializer = UserSerializer(verified_user)

        assert serializer.data["email"] == verified_user.email
        assert serializer.data["is_active"] == verified_user.is_active
        assert "password" not in serializer.data

@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Test ChangePasswordSerializer"""

    def test_valid_data(self, verified_user, rf):
        """Test serializer with valid data"""
        request = rf.post("/fake-url/")
        request.user = verified_user

        data = {
            "current_password": "password123",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "NewStrongP@ssw0rd",
        }

        serializer = ChangePasswordSerializer(data=data, context={"request": request})

        assert serializer.is_valid()

    def test_wrong_current_password(self, verified_user, rf):
        """Test serializer with wrong current password"""
        request = rf.post("/fake-url/")
        request.user = verified_user

        data = {
            "current_password": "wrongpassword",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "NewStrongP@ssw0rd",
        }

        serializer = ChangePasswordSerializer(data=data, context={"request": request})

        assert not serializer.is_valid()
        assert "current_password" in serializer.errors

    def test_mismatched_new_passwords(self, verified_user, rf):
        """Test serializer with mismatched new passwords"""
        request = rf.post("/fake-url/")
        request.user = verified_user

        data = {
            "current_password": "password123",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "DifferentPassword",
        }

        serializer = ChangePasswordSerializer(data=data, context={"request": request})

        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
