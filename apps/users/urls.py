from django.urls import path

from apps.users.views.profile_views import RoleView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    RefreshTokenView,
    RegisterView,
    RequestPasswordResetEmailView,
    ResendVerificationEmailView,
    UserProfileView,
    UserSkillView,
    UserView,
    VerifyEmailView,
    SkillView
)

app_name = "users"

urlpatterns = [
    # Authentication endpoints
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/<uuid:token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("me/", UserView.as_view(), name="user_profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
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
    path(
        "resend-verification-email/",
        ResendVerificationEmailView.as_view(),
        name="resend_verification_email",
    ),
    # Profile URLs
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path(
        "profile/skills/",
        UserSkillView.as_view(http_method_names=["get", "post"]),
        name="user_skills",
    ),
    path(
        "profile/skills/<int:skill_id>/",
        UserSkillView.as_view(http_method_names=["delete"]),
        name="delete_user_skill",
    ),

    # Skill URLs
    path("skills/", SkillView.as_view(), name="skills"),

    # Role URLs
    path("roles/", RoleView.as_view(), name="roles"),

]
