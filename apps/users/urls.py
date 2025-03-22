from django.urls import path
from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    RegisterView,
    RequestPasswordResetEmailView,
    ResendVerificationEmailView,
    UserProfileView,
    VerifyEmailView,
    RefreshTokenView
)

app_name = "users"

urlpatterns = [
    # Authentication endpoints
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/<uuid:token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    # User profile endpoints
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    # Password reset endpoints
    path(
        "password-reset/request/",
        RequestPasswordResetEmailView.as_view(),
        name="request_password_reset",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path('resend-verification-email/', ResendVerificationEmailView.as_view(), name='resend_verification_email'),

]
