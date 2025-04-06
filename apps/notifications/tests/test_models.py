import pytest

from apps.notifications.models import Notification, NotificationType


@pytest.mark.django_db
class TestNotificationModel:
    """Test Notification model"""

    def test_create_notification(self, user):
        """Test creating a notification"""
        notification = Notification.objects.create(
            recipient=user,
            type=NotificationType.SYSTEM_UPDATE,
            title="Test Notification",
            message="This is a test notification",
        )

        assert notification.recipient == user
        assert notification.type == NotificationType.SYSTEM_UPDATE
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.read is False  # Default value
        assert notification.created_at is not None
        assert notification.related_project is None
        assert notification.related_user is None
        assert notification.data is None

    def test_notification_str_representation(self, notification):
        """Test notification string representation"""
        expected_str = f"{notification.recipient.email} - {notification.title} - {notification.created_at}"
        assert str(notification) == expected_str

    def test_notification_ordering(self, user):
        """Test notifications are ordered by created_at descending"""
        # Create older notification
        older = Notification.objects.create(
            recipient=user,
            type=NotificationType.SYSTEM_UPDATE,
            title="Older Notification",
            message="This is an older notification",
        )

        # Create newer notification
        newer = Notification.objects.create(
            recipient=user,
            type=NotificationType.SYSTEM_UPDATE,
            title="Newer Notification",
            message="This is a newer notification",
        )

        # Get ordered notifications
        notifications = Notification.objects.filter(recipient=user)

        # The first notification should be the newer one
        assert notifications.first() == newer
        assert notifications.last() == older
