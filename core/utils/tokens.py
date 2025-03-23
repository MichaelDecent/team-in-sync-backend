from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Generate custom tokens with user details encoded in the payload
    """
    refresh = RefreshToken.for_user(user)

    refresh["first_name"] = user.first_name
    refresh["last_name"] = user.last_name
    refresh["email"] = user.email
    refresh["is_verified"] = user.email_verified

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
