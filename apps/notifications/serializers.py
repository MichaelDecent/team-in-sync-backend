from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "read",
            "created_at",
            "related_project",
            "related_user",
            "data",
        ]
        read_only_fields = [
            "id",
            "type",
            "title",
            "message",
            "created_at",
            "related_project",
            "related_user",
            "data",
        ]
