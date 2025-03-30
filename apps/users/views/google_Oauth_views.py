import requests
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.users.models import SocialProvider, User, UserProfile, UserSocialAuth
from core.utils.api_response import APIResponse
from core.utils.tokens import get_tokens_for_user


def get_google_user_info_from_token(token):
    """
    Get user info from Google using a token.
    Returns user info or raises an exception with error message.
    """
    if not token:
        raise ValueError("Token is required")

    # Get user info from Google
    google_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    user_info_response = requests.get(google_url)

    if user_info_response.status_code != 200:
        raise ValueError(
            f"Failed to get user info from Google: {user_info_response.text}"
        )

    user_info = user_info_response.json()

    # Convert email_verified from string to boolean
    email_verified = user_info.get("email_verified", False)
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"

    # Extract and return necessary user information
    return {
        "google_user_id": user_info.get("sub"),
        "email": user_info.get("email"),
        "first_name": user_info.get("given_name", ""),
        "last_name": user_info.get("family_name", ""),
        "profile_picture": user_info.get("picture"),
        "email_verified": email_verified,  # Now a proper boolean
    }


@extend_schema(tags=["OAuth"])
class GoogleOAuthView(APIView):
    """View for Google OAuth authentication with registration"""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="oauth_google_signup",
        description="Authenticate with Google OAuth (with auto-registration)",
        request={"application/json": {"properties": {"token": {"type": "string"}}}},
    )
    def post(self, request):
        """Process Google OAuth authentication with auto-registration"""
        token = request.data.get("token")
        if not token:
            return APIResponse.bad_request("Access token is required")

        try:
            user_info = get_google_user_info_from_token(token)

            print(user_info)

            google_user_id = user_info["google_user_id"]
            email = user_info["email"]
            first_name = user_info["first_name"]
            last_name = user_info["last_name"]
            email_verified = user_info["email_verified"]

            if not email or not google_user_id:
                return APIResponse.bad_request(
                    "Email and user ID are required from Google"
                )

            try:
                social_auth = UserSocialAuth.objects.get(
                    provider=SocialProvider.GOOGLE, provider_user_id=google_user_id
                )
                user = social_auth.user

                if social_auth.provider_email != email:
                    social_auth.provider_email = email
                    social_auth.save()

                tokens = get_tokens_for_user(user)

                return APIResponse.success(
                    data=tokens,
                    message="Login successful",
                )

            except UserSocialAuth.DoesNotExist:
                user_exists = User.objects.filter(email=email).exists()

                if user_exists:
                    user = User.objects.get(email=email)

                    UserSocialAuth.objects.create(
                        user=user,
                        provider=SocialProvider.GOOGLE,
                        provider_user_id=google_user_id,
                        provider_email=email,
                    )

                    tokens = get_tokens_for_user(user)

                    return APIResponse.success(
                        data=tokens,
                        message="Existing account linked with Google successfully",
                    )

                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=None,
                    )

                    UserSocialAuth.objects.create(
                        user=user,
                        provider=SocialProvider.GOOGLE,
                        provider_user_id=google_user_id,
                        provider_email=email,
                    )

                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={"first_name": first_name, "last_name": last_name},
                    )

                    if created:
                        profile.first_name = first_name
                        profile.last_name = last_name
                    user.email_verified = email_verified
                    user.save()
                    tokens = get_tokens_for_user(user)

                    return APIResponse.success(
                        data=tokens,
                        status_code=status.HTTP_201_CREATED,
                        message="Account created successfully",
                    )
        except ValueError as e:
            return APIResponse.bad_request(str(e))


@extend_schema(tags=["OAuth"])
class GoogleOAuthLoginView(APIView):
    """View for Google OAuth login only (no auto-registration)"""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="oauth_google_login",
        description="Login with Google OAuth (no auto-registration)",
        request={"application/json": {"properties": {"token": {"type": "string"}}}},
    )
    def post(self, request):
        """Process Google OAuth login without auto-registration"""
        token = request.data.get("token")
        if not token:
            return APIResponse.bad_request("Access token is required")

        try:
            user_info = get_google_user_info_from_token(token)

            google_user_id = user_info["google_user_id"]
            email = user_info["email"]

            if not email or not google_user_id:
                return APIResponse.bad_request(
                    "Email and user ID are required from Google"
                )

            try:
                social_auth = UserSocialAuth.objects.get(
                    provider=SocialProvider.GOOGLE, provider_user_id=google_user_id
                )
                user = social_auth.user

                if social_auth.provider_email != email:
                    social_auth.provider_email = email
                    social_auth.save()

                tokens = get_tokens_for_user(user)

                return APIResponse.success(
                    data=tokens,
                    message="Login successful",
                )

            except UserSocialAuth.DoesNotExist:
                if User.objects.filter(email=email).exists():
                    user = User.objects.get(email=email)

                    UserSocialAuth.objects.create(
                        user=user,
                        provider=SocialProvider.GOOGLE,
                        provider_user_id=google_user_id,
                        provider_email=email,
                    )

                    tokens = get_tokens_for_user(user)

                    return APIResponse.success(
                        data=tokens,
                        message="Existing account linked with Google successfully",
                    )

                return APIResponse.not_found(
                    "No account found with this email. Please sign up first."
                )

        except ValueError as e:
            return APIResponse.bad_request(str(e))
