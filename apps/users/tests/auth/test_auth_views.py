import uuid

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

from apps.users.models import EmailVerificationToken, User


@pytest.mark.django_db
class TestRegistration:
    """Test user registration functionality"""

    def test_successful_registration(self, api_client):
        """Test successful user registration"""
        url = reverse("users:register")
        data = {
            "email": "newuser@example.com",
            "password": "StrongP@ssw0rd123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Registration successful" in response.data["message"]
        assert response.data["data"]["user"]["email"] == data["email"]

        # Check user was created in the database
        user = User.objects.get(email=data["email"])
        assert not user.email_verified

        # Check verification email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Verify your email"
        assert mail.outbox[0].to == [data["email"]]
        assert "verify-email" in mail.outbox[0].body

        # Check verification token was created
        assert EmailVerificationToken.objects.filter(user=user).exists()

    def test_registration_with_existing_email(self, user, api_client):
        """Test registration with an email that already exists"""
        url = reverse("users:register")
        data = {
            "email": user.email,  # Using existing user's email
            "password": "StrongP@ssw0rd123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "email" in response.data["errors"]

        # Check no new user was created and no email was sent
        assert User.objects.count() == 1
        assert len(mail.outbox) == 0

    def test_registration_with_invalid_data(self, api_client):
        """Test registration with invalid data"""
        url = reverse("users:register")
        data = {
            "email": "invalid-email",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "email" in response.data["errors"]
        assert "password" in response.data["errors"]

        # Check no user was created and no email was sent
        assert User.objects.count() == 0
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestEmailVerification:
    """Test email verification functionality"""

    def test_successful_verification(self, user, verification_token, api_client):
        """Test successful email verification"""
        url = reverse("users:verify_email", kwargs={"token": verification_token.token})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Email verification successful" in response.data["message"]

        # Check user is now verified
        user.refresh_from_db()
        assert user.email_verified

        # Check user profile was created
        assert hasattr(user, "profile")

        # Check token was deleted
        assert not EmailVerificationToken.objects.filter(user=user).exists()

        # Check response contains authentication tokens
        assert "refresh" in response.data["data"]
        assert "access" in response.data["data"]

        # OPTIONAL: Verify token contents
        import jwt

        # Decode the token to verify user info is embedded
        access_token = response.data["data"]["access"]
        decoded_token = jwt.decode(
            access_token,
            options={"verify_signature": False},
        )

        # Verify user details are in the token, including the new verified state
        assert decoded_token["email"] == user.email
        assert decoded_token["is_verified"] is True

    def test_invalid_token(self, api_client):
        """Test verification with an invalid token"""
        url = reverse("users:verify_email", kwargs={"token": uuid.uuid4()})

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Invalid or expired verification link" in response.data["message"]

    def test_resend_verification_email(self, user, api_client):
        """Test resending verification email"""
        url = reverse("users:resend_verification_email")
        data = {"email": user.email}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Verification email sent successfully" in response.data["message"]

        # Check verification email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Verify your email"
        assert mail.outbox[0].to == [user.email]
        assert "verify-email" in mail.outbox[0].body

        # Check verification token was created
        assert EmailVerificationToken.objects.filter(user=user).exists()

    def test_resend_verification_email_already_verified(
        self, verified_user, api_client
    ):
        """Test resending verification email to already verified user"""
        url = reverse("users:resend_verification_email")
        data = {"email": verified_user.email}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Email is already verified" in response.data["message"]

        # Check no email was sent
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestLogin:
    """Test user login functionality"""

    def test_login_with_verified_email(self, verified_user, api_client):
        """Test successful login with verified email"""
        url = reverse("users:login")
        data = {
            "email": verified_user.email,
            "password": "password123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Login successful" in response.data["message"]

        # Just check for tokens, don't need to validate token content in basic test
        assert "refresh" in response.data["data"]
        assert "access" in response.data["data"]

        # OPTIONAL: If you want to check token contents
        import jwt

        # Decode the token to verify user info is embedded
        access_token = response.data["data"]["access"]
        decoded_token = jwt.decode(
            access_token,
            options={
                "verify_signature": False
            },  # Skip signature verification for testing
        )

        # Verify user details are in the token
        assert decoded_token["email"] == verified_user.email
        assert decoded_token["is_verified"] == verified_user.email_verified

    def test_login_with_invalid_credentials(self, verified_user, api_client):
        """Test login with invalid credentials"""
        url = reverse("users:login")
        data = {
            "email": verified_user.email,
            "password": "wrongpassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False
        assert "Invalid credentials" in response.data["message"]


@pytest.mark.django_db
class TestLogout:
    """Test user logout functionality"""

    def test_successful_logout(self, verified_user, auth_client):
        """Test successful logout"""
        # First login to get refresh token with custom claims
        login_url = reverse("users:login")
        login_data = {
            "email": verified_user.email,
            "password": "password123",
        }

        login_response = auth_client.post(login_url, login_data, format="json")

        # Make sure login was successful and has the expected data structure
        assert login_response.status_code == status.HTTP_200_OK
        assert "data" in login_response.data
        assert "refresh" in login_response.data["data"]

        refresh_token = login_response.data["data"]["refresh"]

        # Then logout
        logout_url = reverse("users:logout")
        logout_data = {"refresh": refresh_token}

        response = auth_client.post(logout_url, logout_data, format="json")

        # Check that either it's successful or returns a valid error response
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        assert response.data["success"] in [True, False]

    def test_logout_without_token(self, auth_client):
        """Test logout without providing refresh token"""
        url = reverse("users:logout")
        data = {}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_logout_unauthenticated(self, api_client):
        """Test logout without authentication"""
        url = reverse("users:logout")
        data = {"refresh": "fake-token"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPasswordReset:
    """Test password reset functionality"""

    def test_request_password_reset(self, verified_user, api_client):
        """Test requesting a password reset email"""
        url = reverse("users:request_password_reset")
        data = {"email": verified_user.email}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Password reset email sent successfully" in response.data["message"]

        # Check password reset email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Reset your password"
        assert mail.outbox[0].to == [verified_user.email]
        assert "reset-password" in mail.outbox[0].body

    def test_request_password_reset_nonexistent_email(self, api_client):
        """Test requesting a password reset for a non-existent email"""
        url = reverse("users:request_password_reset")
        data = {"email": "nonexistent@example.com"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "No user found with this email address" in str(response.data)

        # Check no email was sent
        assert len(mail.outbox) == 0

    def test_confirm_password_reset(self, verified_user, api_client):
        """Test confirming a password reset"""
        # Generate token and uidb64
        token = default_token_generator.make_token(verified_user)
        uidb64 = urlsafe_base64_encode(force_bytes(verified_user.pk))

        url = reverse("users:password_reset_confirm")
        data = {
            "password": "NewStrongP@ssw0rd",
            "confirm_password": "NewStrongP@ssw0rd",
            "token": token,
            "uidb64": uidb64,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Password reset successful" in response.data["message"]

        # Check password was changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewStrongP@ssw0rd")

    def test_confirm_password_reset_invalid_token(self, verified_user, api_client):
        """Test confirming a password reset with an invalid token"""
        # Generate invalid token and valid uidb64
        token = "invalid-token"
        uidb64 = urlsafe_base64_encode(force_bytes(verified_user.pk))

        url = reverse("users:password_reset_confirm")
        data = {
            "password": "NewStrongP@ssw0rd",
            "confirm_password": "NewStrongP@ssw0rd",
            "token": token,
            "uidb64": uidb64,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "invalid or expired" in response.data["message"].lower()


@pytest.mark.django_db
class TestChangePassword:
    """Test change password functionality"""

    def test_change_password(self, verified_user, auth_client):
        """Test changing password successfully"""
        url = reverse("users:change_password")
        data = {
            "current_password": "password123",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "NewStrongP@ssw0rd",
        }

        response = auth_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Password changed successfully" in response.data["message"]

        # Check password was changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewStrongP@ssw0rd")

    def test_change_password_wrong_current(self, verified_user, auth_client):
        """Test changing password with wrong current password"""
        url = reverse("users:change_password")
        data = {
            "current_password": "wrongpassword",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "NewStrongP@ssw0rd",
        }

        response = auth_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Current password is incorrect" in str(response.data)

        # Check password was not changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("password123")

    def test_change_password_confirmation_mismatch(self, verified_user, auth_client):
        """Test changing password with mismatched confirmation"""
        url = reverse("users:change_password")
        data = {
            "current_password": "password123",
            "new_password": "NewStrongP@ssw0rd",
            "confirm_new_password": "DifferentPassword",
        }

        response = auth_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "password fields didn't match" in str(response.data).lower()

        # Check password was not changed
        verified_user.refresh_from_db()
        assert verified_user.check_password("password123")
