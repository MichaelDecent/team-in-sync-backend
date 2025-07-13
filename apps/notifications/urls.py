from django.urls import path

from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    UnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path(
        "mark-all-read/", MarkAllNotificationsReadView.as_view(), name="mark-all-read"
    ),
    path(
        "<int:notification_id>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "<int:notification_id>/mark-read/",
        MarkNotificationReadView.as_view(),
        name="mark-read",
    ),
]
