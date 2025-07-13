from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.views import APIView

from core.utils.api_response import APIResponse

from .models import Notification, NotificationType
from .serializers import NotificationSerializer


@extend_schema(tags=["Notifications"])
class NotificationListView(APIView):
    """View for listing notifications with optional filtering"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="List all notifications for the current user with optional filtering",
        parameters=[
            OpenApiParameter(
                name="type",
                description="Filter by notification type",
                required=False,
                type=str,
                enum=[choice[0] for choice in NotificationType.choices],
            ),
            OpenApiParameter(
                name="read",
                description="Filter by read status",
                required=False,
                type=bool,
            ),
        ],
    )
    def get(self, request):
        """Get filtered list of notifications"""
        queryset = Notification.objects.filter(recipient=request.user)

        notification_type = request.query_params.get("type", None)
        if notification_type and notification_type in [
            choice[0] for choice in NotificationType.choices
        ]:
            queryset = queryset.filter(type=notification_type)

        read_status = request.query_params.get("read", None)
        if read_status is not None:
            read_bool = read_status.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(read=read_bool)

        serializer = NotificationSerializer(queryset, many=True)
        return APIResponse.success(data=serializer.data)


@extend_schema(tags=["Notifications"])
class NotificationDetailView(APIView):
    """View for retrieving and deleting individual notifications"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(description="Retrieve a specific notification")
    def get(self, request, notification_id):
        """Get a specific notification"""
        try:
            notification = Notification.objects.get(
                id=notification_id, recipient=request.user
            )
        except Notification.DoesNotExist:
            return APIResponse.not_found("Notification not found")

        serializer = NotificationSerializer(notification)
        return APIResponse.success(data=serializer.data)

    @extend_schema(description="Delete a specific notification")
    def delete(self, request, notification_id):
        """Delete a notification"""
        try:
            notification = Notification.objects.get(
                id=notification_id, recipient=request.user
            )
        except Notification.DoesNotExist:
            return APIResponse.not_found("Notification not found")

        notification.delete()
        return APIResponse.success(message="Notification deleted successfully")


@extend_schema(tags=["Notifications"])
class MarkNotificationReadView(APIView):
    """View for marking a notification as read"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(description="Mark a notification as read")
    def patch(self, request, notification_id):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id, recipient=request.user
            )
        except Notification.DoesNotExist:
            return APIResponse.not_found("Notification not found")

        notification.read = True
        notification.save()
        return APIResponse.success(data=NotificationSerializer(notification).data)


@extend_schema(tags=["Notifications"])
class MarkAllNotificationsReadView(APIView):
    """View for marking all notifications as read"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(description="Mark all notifications as read")
    def post(self, request):
        """Mark all notifications as read"""
        queryset = Notification.objects.filter(recipient=request.user)
        queryset.update(read=True)
        return APIResponse.success(message="All notifications marked as read")


@extend_schema(tags=["Notifications"])
class UnreadCountView(APIView):
    """View for getting unread notification count"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(description="Get count of unread notifications")
    def get(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return APIResponse.success(data={"count": count})
