from apps.notifications.models import Notification, NotificationType
from apps.users.models import User


class NotificationService:
    """Service for creating and managing notifications"""

    @staticmethod
    def create_join_request_notification(membership):
        """Create a notification when a user requests to join a project"""
        project = membership.project
        requester = membership.user
        owner = project.owner

        # Access role name through the relationship
        role_name = (
            membership.role.role.name
            if membership.role and membership.role.role
            else "Unknown Role"
        )

        print(f"members role {role_name}")

        Notification.objects.create(
            recipient=owner,
            type=NotificationType.JOIN_REQUEST,
            title=f"New join request for {project.title}",
            message=f"{requester.email} has requested to join your project as a {role_name}.",
            related_project=project,
            related_user=requester,
            data={
                "membership_id": membership.id,
                "role_id": membership.role.id,
            },
        )

    @staticmethod
    def create_request_response_notification(membership, accepted=True):
        """Create a notification when a join request is accepted/rejected"""
        project = membership.project
        requester = membership.user

        # Fix role name access
        role_name = (
            membership.role.role.name
            if membership.role and membership.role.role
            else "Unknown Role"
        )

        notification_type = (
            NotificationType.REQUEST_ACCEPTED
            if accepted
            else NotificationType.REQUEST_REJECTED
        )
        title = f"Request {'accepted' if accepted else 'rejected'} for {project.title}"
        message = f"Your request to join {project.title} as a {role_name} has been {'accepted' if accepted else 'rejected'}."

        # Rest of the method...
        Notification.objects.create(
            recipient=requester,
            type=notification_type,
            title=title,
            message=message,
            related_project=project,
            related_user=project.owner,
        )

    @staticmethod
    def create_system_notification(title, message, recipients=None):
        """Create a system-wide notification for all users or specific recipients"""
        if recipients is None:
            recipients = User.objects.filter(is_active=True)

        notifications = [
            Notification(
                recipient=recipient,
                type=NotificationType.SYSTEM_UPDATE,
                title=title,
                message=message,
            )
            for recipient in recipients
        ]

        Notification.objects.bulk_create(notifications)
