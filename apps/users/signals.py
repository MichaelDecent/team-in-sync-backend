from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile_when_verified(sender, instance, created, **kwargs):
    """
    Create a profile when a user is verified
    """
    # If user is verified and doesn't have a profile yet, create one
    if instance.email_verified and not hasattr(instance, "profile"):
        UserProfile.objects.create(user=instance)
