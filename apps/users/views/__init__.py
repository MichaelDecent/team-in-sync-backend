from .auth_views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    RefreshTokenView,
    RegisterView,
    RequestPasswordResetEmailView,
    ResendVerificationEmailView,
    UserView,
    VerifyEmailView,
)
from .google_Oauth_views import (
    GoogleOAuthLoginView,
    GoogleOAuthView,
)
from .profile_views import (
    RoleView,
    SkillView,
    UserProfileView,
    UserSkillView,
)

__all__ = [
    "RegisterView",
    "LoginView",
    "LogoutView",
    "VerifyEmailView",
    "ChangePasswordView",
    "RefreshTokenView",
    "UserView",
    "RequestPasswordResetEmailView",
    "PasswordResetConfirmView",
    "ResendVerificationEmailView",
    "UserProfileView",
    "UserSkillView",
    "SkillView",
    "RoleView",
    "GoogleOAuthView",
    "GoogleOAuthLoginView",
]
