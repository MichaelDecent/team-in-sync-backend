from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import EmailVerificationToken
from core.utils.response import APIResponse

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResetPasswordEmailSerializer,
    SetNewPasswordSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    View for user registration
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user but set is_active to False until email is verified
        user = serializer.save()

        # Create verification token
        verification_token = EmailVerificationToken.objects.create(user=user)

        # Send verification email
        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}/"
        )

        email_body = f"""
        Hi {user.first_name},

        Thank you for registering with our platform. Please click on the link below to verify your email:

        {verification_url}

        This link will expire in 24 hours.
        """

        send_mail(
            "Verify your email",
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return APIResponse.success(
            data={"user": UserSerializer(user).data},
            message="Registration successful. Please check your email to verify your account.",
        )


class VerifyEmailView(APIView):
    """
    View for verifying user email
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            user = verification_token.user

            # Mark email as verified
            user.email_verified = True
            user.save()

            # Delete the token
            verification_token.delete()

            # Generate tokens for login
            refresh = RefreshToken.for_user(user)

            return APIResponse(
                data={
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(user).data,
                },
                message="Email verification successful",
            )

        except EmailVerificationToken.DoesNotExist:
            return APIResponse.bad_request(error="Invalid or expired verification link")


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
            return APIResponse.bad_request(errors=serializer.errors)

        user = serializer.validated_data["user"]
        if not user.email_verified:
            return APIResponse.forbidden(message="Email is not verified")

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return APIResponse.success(
            data={
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            message="Login successful",
        )


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


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating user profile
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    View for changing user password
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return APIResponse.success(message="Password changed successfully")


class RequestPasswordResetEmailView(generics.GenericAPIView):
    """
    View for requesting password reset email
    """

    serializer_class = ResetPasswordEmailSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        # Generate token
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Create reset link - replace with your frontend URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"

        # Send email
        email_body = f"Hi {user.first_name},\n\nUse this link to reset your password:\n{reset_url}\n\nThis link is valid for 24 hours."
        send_mail(
            "Reset your password",
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return APIResponse.success(message="Password reset email sent successfully")


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    View for confirming password reset
    """

    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(
                urlsafe_base64_decode(serializer.validated_data["uidb64"])
            )
            user = User.objects.get(pk=user_id)
            token = serializer.validated_data["token"]

            if not default_token_generator.check_token(user, token):
                return APIResponse.bad_request(error="Token is invalid or expired")

            user.set_password(serializer.validated_data["password"])
            user.save()

            return APIResponse.success(message="Password reset successful")
        except Exception:
            return APIResponse.bad_request(error="Invalid or expired reset link")


class ResendVerificationEmailView(APIView):
    """
    View for resending verification emails
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return APIResponse.bad_request(error="Email is required")
        try:
            user = User.objects.get(email=email)

            # Check if already verified
            if user.email_verified:
                return APIResponse.bad_request(error="Email is already verified")

            # Delete existing tokens
            EmailVerificationToken.objects.filter(user=user).delete()

            # Create new verification token
            verification_token = EmailVerificationToken.objects.create(user=user)

            # Send verification email
            verification_url = (
                f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}/"
            )

            email_body = f"""
            Hi {user.first_name},

            Please click on the link below to verify your email:
            
            {verification_url}
            
            This link will expire in 24 hours.
            """

            send_mail(
                "Verify your email",
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return APIResponse.success(
                message="Verification email sent successfully. Please check your email."
            )
        except User.DoesNotExist:
            return APIResponse.bad_request(error="User not found")
