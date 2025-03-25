from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Generate custom tokens with user details encoded in the payload
    """
    refresh = RefreshToken.for_user(user)

    refresh["email"] = user.email
    refresh["is_verified"] = user.email_verified

    has_profile = hasattr(user, "profile")
    refresh["is_profile_complete"] = False

    if has_profile:
        refresh["is_profile_complete"] = user.profile.is_complete()

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
