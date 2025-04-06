from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from core.utils.api_response import APIResponse

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(description="List all notifications for the current user"),
    mark_all_read=extend_schema(description="Mark all notifications as read"),
)
@extend_schema(tags=["Notifications"])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notifications"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter notifications to only show the current user's"""
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["patch"])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return APIResponse.success(data=NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        queryset = self.get_queryset()
        queryset.update(read=True)
        return APIResponse.success(message="All notifications marked as read")

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(read=False).count()
        return APIResponse.success(data={"count": count})
