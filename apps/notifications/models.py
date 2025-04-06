from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


class NotificationType(models.TextChoices):
    JOIN_REQUEST = "join_request", _("Join Request")
    REQUEST_ACCEPTED = "request_accepted", _("Request Accepted")
    REQUEST_REJECTED = "request_rejected", _("Request Rejected")
    SYSTEM_UPDATE = "system_update", _("System Update")
    PROJECT_UPDATE = "project_update", _("Project Update")


class Notification(models.Model):
    """Model for user notifications"""

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=100)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional reference fields
    related_project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_notifications",
    )
    data = models.JSONField(null=True, blank=True)  # For additional context

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.email} - {self.title} - {self.created_at}"
