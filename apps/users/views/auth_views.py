from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.models import EmailVerificationToken
from apps.users.models.profile_models import UserProfile
from core.utils.api_response import APIResponse
from core.utils.tokens import get_tokens_for_user

from ..serializers.auth_serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
    ResetPasswordEmailSerializer,
    SetNewPasswordSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(tags=["Authentication"])
class RegisterView(generics.CreateAPIView):
    """
    View for user registration
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        user = serializer.save()

        verification_token = EmailVerificationToken.objects.create(user=user)

        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}/"
        )

        try:
            context = {"user": user, "verification_url": verification_url}
            html_message = render_to_string("emails/verification_email.html", context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject="Verify your email",
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return APIResponse.success(
                data={"user": UserSerializer(user).data},
                message="Registration successful. Please check your email to verify your account.",
            )
        except Exception as e:
            print(f"Error: {e}")
            if "user" in locals():
                user.delete()
            return APIResponse.bad_request(
                message="Registration failed. Please try again later."
            )


@extend_schema(tags=["Authentication"])
class VerifyEmailView(APIView):
    """
    View for verifying user email
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            user = verification_token.user

            user.email_verified = True
            user.save()

            UserProfile.objects.get_or_create(user=user)

            verification_token.delete()

            tokens = get_tokens_for_user(user)

            return APIResponse.success(
                data={
                    "refresh": tokens["refresh"],
                    "access": tokens["access"],
                },
                message="Email verification successful",
            )

        except EmailVerificationToken.DoesNotExist:
            return APIResponse.bad_request("Invalid or expired verification link")


@extend_schema(tags=["Authentication"])
class LoginView(APIView):
    """
    View for user login
    """

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        user = serializer.validated_data["user"]
        if not user.email_verified:
            return APIResponse.forbidden(message="Email is not verified")

        tokens = get_tokens_for_user(user)

        return APIResponse.success(
            data={
                "refresh": tokens["refresh"],
                "access": tokens["access"],
            },
            message="Login successful",
        )


@extend_schema(tags=["Authentication"])
class LogoutView(APIView):
    """
    View for user logout - blacklist the refresh token
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return APIResponse.success(message="Logout successful")
        except Exception as e:
            return APIResponse.bad_request(message=str(e))


@extend_schema(tags=["Authentication"])
class UserView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating user
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Authentication"])
class ChangePasswordView(generics.UpdateAPIView):
    """
    View for changing user password
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return APIResponse.success(message="Password changed successfully")


@extend_schema(tags=["Authentication"])
class RequestPasswordResetEmailView(generics.GenericAPIView):
    """
    View for requesting password reset email
    """

    serializer_class = ResetPasswordEmailSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        # Generate token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"

        try:
            context = {"user": user, "reset_url": reset_url}
            html_message = render_to_string("emails/password_reset.html", context)
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject="Reset your password",
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return APIResponse.bad_request(str(e))

        return APIResponse.success(message="Password reset email sent successfully")


@extend_schema(tags=["Authentication"])
class PasswordResetConfirmView(generics.GenericAPIView):
    """
    View for confirming password reset
    """

    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        try:
            user_id = force_str(
                urlsafe_base64_decode(serializer.validated_data["uidb64"])
            )
            user = User.objects.get(pk=user_id)
            token = serializer.validated_data["token"]

            if not default_token_generator.check_token(user, token):
                return APIResponse.bad_request("Token is invalid or expired")

            user.set_password(serializer.validated_data["password"])
            user.save()

            return APIResponse.success(message="Password reset successful")
        except Exception:
            return APIResponse.bad_request("Invalid or expired reset link")


@extend_schema(tags=["Authentication"])
class ResendVerificationEmailView(APIView):
    """
    View for resending verification emails
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return APIResponse.bad_request(serializer.errors)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            if user.email_verified:
                return APIResponse.bad_request("Email is already verified")

            EmailVerificationToken.objects.filter(user=user).delete()

            verification_token = EmailVerificationToken.objects.create(user=user)

            verification_url = (
                f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}/"
            )

            try:
                context = {"user": user, "verification_url": verification_url}
                html_message = render_to_string(
                    "emails/verification_email.html", context
                )
                plain_message = strip_tags(html_message)

                send_mail(
                    subject="Verify your email",
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                return APIResponse.success(
                    message="Verification email sent successfully. Please check your email."
                )
            except Exception as e:
                return APIResponse.bad_request(str(e))

        except User.DoesNotExist:
            return APIResponse.bad_request("User not found")


@extend_schema(tags=["Authentication"])
class RefreshTokenView(TokenRefreshView):
    pass
