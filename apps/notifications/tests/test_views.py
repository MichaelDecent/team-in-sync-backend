import pytest
from django.urls import reverse
from rest_framework import status

from apps.notifications.models import Notification, NotificationType


@pytest.mark.django_db
class TestNotificationViewSet:
    """Test NotificationViewSet"""

    def test_list_notifications(
        self, auth_client, user, user_notification, other_user_notification
    ):
        """Test listing notifications (should only include the user's notifications)"""
        url = reverse("notifications:notifications-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == user_notification.id
        assert response.data[0]["title"] == user_notification.title

        # Check that other user's notifications are not included
        for notification in response.data:
            assert notification["id"] != other_user_notification.id

    def test_mark_notification_read(self, auth_client, user_notification):
        """Test marking a notification as read"""
        assert user_notification.read is False  # Should be unread initially

        url = reverse(
            "notifications:notifications-mark-read", kwargs={"pk": user_notification.id}
        )
        response = auth_client.patch(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["id"] == user_notification.id
        assert response.data["data"]["read"] is True

        # Check database was updated
        user_notification.refresh_from_db()
        assert user_notification.read is True

    def test_mark_all_read(self, auth_client, user):
        """Test marking all notifications as read"""
        # Create multiple unread notifications
        for i in range(3):
            Notification.objects.create(
                recipient=user,
                type=NotificationType.SYSTEM_UPDATE,
                title=f"Notification {i}",
                message=f"This is test notification {i}",
                read=False,
            )

        # Verify all are unread
        assert Notification.objects.filter(recipient=user, read=False).count() == 3

        # Mark all as read
        url = reverse("notifications:notifications-mark-all-read")
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "All notifications marked as read" in response.data["message"]

        # Check all notifications were marked as read
        assert Notification.objects.filter(recipient=user, read=False).count() == 0
        assert Notification.objects.filter(recipient=user, read=True).count() == 3

    def test_unread_count(self, auth_client, user):
        """Test getting count of unread notifications"""
        # Create 2 unread and 1 read notification
        for i in range(2):
            Notification.objects.create(
                recipient=user,
                type=NotificationType.SYSTEM_UPDATE,
                title=f"Unread Notification {i}",
                message=f"This is unread notification {i}",
                read=False,
            )

        Notification.objects.create(
            recipient=user,
            type=NotificationType.SYSTEM_UPDATE,
            title="Read Notification",
            message="This is a read notification",
            read=True,
        )

        # Get unread count
        url = reverse("notifications:notifications-unread-count")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["count"] == 2

    def test_cannot_access_other_user_notification(
        self, auth_client, other_user_notification
    ):
        """Test that a user cannot access another user's notification"""
        url = reverse(
            "notifications:notifications-detail",
            kwargs={"pk": other_user_notification.id},
        )
        response = auth_client.get(url)

        # Should return 404 rather than 403 for security reasons
        assert response.status_code == status.HTTP_404_NOT_FOUND
