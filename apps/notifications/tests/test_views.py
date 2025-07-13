import pytest
from django.urls import reverse
from rest_framework import status

from apps.notifications.models import Notification, NotificationType


@pytest.mark.django_db
class TestNotificationViews:
    """Test Notification APIViews"""

    def test_list_notifications(
        self, auth_client, user, user_notification, other_user_notification
    ):
        """Test listing notifications (should only include the user's notifications)"""
        url = reverse("notifications:notification-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) == 1
        assert response.data["data"][0]["id"] == user_notification.id
        assert response.data["data"][0]["title"] == user_notification.title

        # Check that other user's notifications are not included
        for notification in response.data["data"]:
            assert notification["id"] != other_user_notification.id

    def test_mark_notification_read(self, auth_client, user_notification):
        """Test marking a notification as read"""
        assert user_notification.read is False  # Should be unread initially

        url = reverse(
            "notifications:mark-read", kwargs={"notification_id": user_notification.id}
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
        url = reverse("notifications:mark-all-read")
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
        url = reverse("notifications:unread-count")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["count"] == 2

    def test_cannot_access_other_user_notification(
        self, auth_client, other_user_notification
    ):
        """Test that a user cannot access another user's notification"""
        url = reverse(
            "notifications:notification-detail",
            kwargs={"notification_id": other_user_notification.id},
        )
        response = auth_client.get(url)

        # Should return 404 rather than 403 for security reasons
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_notification(self, auth_client, user_notification):
        """Test deleting a notification"""
        url = reverse(
            "notifications:notification-detail",
            kwargs={"notification_id": user_notification.id},
        )
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "Notification deleted successfully" in response.data["message"]

        # Check notification was deleted from database
        assert not Notification.objects.filter(id=user_notification.id).exists()

    def test_get_notification_detail(self, auth_client, user_notification):
        """Test getting a specific notification"""
        url = reverse(
            "notifications:notification-detail",
            kwargs={"notification_id": user_notification.id},
        )
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["id"] == user_notification.id
        assert response.data["data"]["title"] == user_notification.title
