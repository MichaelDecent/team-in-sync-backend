import pytest

from apps.notifications.models import Notification, NotificationType
from apps.notifications.services import NotificationService
from apps.users.tests.factories import VerifiedUserFactory


@pytest.mark.django_db
class TestNotificationService:
    """Test NotificationService"""

    def test_create_join_request_notification(self, membership, owner):
        """Test creating a join request notification"""
        # Clear any existing notifications
        Notification.objects.all().delete()

        # Create notification
        NotificationService.create_join_request_notification(membership)

        # Check notification was created
        notifications = Notification.objects.all()
        assert notifications.count() == 1

        notification = notifications.first()
        assert notification.recipient == owner
        assert notification.type == NotificationType.JOIN_REQUEST
        assert f"New join request for {membership.project.title}" in notification.title
        assert membership.user.email in notification.message
        assert "designer" in notification.message.lower()
        assert notification.related_project == membership.project
        assert notification.related_user == membership.user
        assert notification.data["membership_id"] == membership.id
        assert notification.data["role_id"] == membership.role.id

    def test_create_request_accepted_notification(self, membership, requester):
        """Test creating a request accepted notification"""
        # Clear any existing notifications
        Notification.objects.all().delete()

        # Create notification
        NotificationService.create_request_response_notification(
            membership, accepted=True
        )

        # Check notification was created
        notifications = Notification.objects.all()
        assert notifications.count() == 1

        notification = notifications.first()
        assert notification.recipient == requester
        assert notification.type == NotificationType.REQUEST_ACCEPTED
        assert "accepted" in notification.title.lower()
        assert membership.project.title in notification.title
        assert "accepted" in notification.message.lower()
        assert membership.project.title in notification.message
        assert "designer" in notification.message.lower()
        assert notification.related_project == membership.project
        assert notification.related_user == membership.project.owner

    def test_create_request_rejected_notification(self, membership, requester):
        """Test creating a request rejected notification"""
        # Clear any existing notifications
        Notification.objects.all().delete()

        # Create notification
        NotificationService.create_request_response_notification(
            membership, accepted=False
        )

        # Check notification was created
        notifications = Notification.objects.all()
        assert notifications.count() == 1

        notification = notifications.first()
        assert notification.recipient == requester
        assert notification.type == NotificationType.REQUEST_REJECTED
        assert "rejected" in notification.title.lower()
        assert "rejected" in notification.message.lower()

    def test_create_system_notification(self):
        """Test creating system notifications for all users"""
        # Create some users
        users = [VerifiedUserFactory() for _ in range(3)]

        # Clear any existing notifications
        Notification.objects.all().delete()

        # Create system notification
        title = "System Maintenance"
        message = "The system will be down for maintenance tomorrow."
        NotificationService.create_system_notification(title, message)

        # Check notifications were created for all users
        notifications = Notification.objects.all()
        assert notifications.count() == len(users)

        # Check notification properties
        for notification in notifications:
            assert notification.type == NotificationType.SYSTEM_UPDATE
            assert notification.title == title
            assert notification.message == message
            assert notification.recipient in users

    def test_create_system_notification_specific_recipients(self):
        """Test creating system notifications for specific recipients"""
        # Create users
        all_users = [VerifiedUserFactory() for _ in range(5)]
        selected_users = all_users[:2]  # Only select first two users

        # Clear any existing notifications
        Notification.objects.all().delete()

        # Create system notification
        title = "Selected Users Only"
        message = "This message is only for selected users."
        NotificationService.create_system_notification(
            title, message, recipients=selected_users
        )

        # Check notifications were created only for selected users
        notifications = Notification.objects.all()
        assert notifications.count() == len(selected_users)

        # Check recipients
        notification_recipients = [n.recipient for n in notifications]
        for user in selected_users:
            assert user in notification_recipients
