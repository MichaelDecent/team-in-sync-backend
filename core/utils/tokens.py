from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Generate custom tokens with user details encoded in the payload
    """
    refresh = RefreshToken.for_user(user)

    refresh["email"] = user.email
    refresh["is_verified"] = user.email_verified
    refresh["has_profile"] = hasattr(user, "profile")

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
