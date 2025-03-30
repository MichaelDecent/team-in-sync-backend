from django.db import models
from django.utils.translation import gettext_lazy as _

from .auth_models import User


class SocialProvider(models.TextChoices):
    """Social login providers"""

    GOOGLE = "google", _("Google")
    # Add other providers like FACEBOOK, GITHUB, etc. if needed


class UserSocialAuth(models.Model):
    """Model for storing social auth provider information"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_auths"
    )
    provider = models.CharField(
        max_length=20, choices=SocialProvider.choices, default=SocialProvider.GOOGLE
    )
    provider_user_id = models.CharField(max_length=255)
    provider_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("provider", "provider_user_id")
        verbose_name = _("user social auth")
        verbose_name_plural = _("user social auths")

    def __str__(self):
        return f"{self.user.email} - {self.provider}"
