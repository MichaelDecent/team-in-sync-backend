from django import forms
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator

from .models import Notification
from .services import NotificationService


class SystemNotificationForm(forms.Form):
    title = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "type", "title", "read", "created_at"]
    list_filter = ["type", "read", "created_at"]
    search_fields = ["title", "message", "recipient__email"]
    readonly_fields = ["type", "created_at"]

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "send_system_notification/",
                self.admin_site.admin_view(self.send_system_notification_view),
                name="send_system_notification",
            ),
        ]
        return custom_urls + urls

    @method_decorator(staff_member_required)
    def send_system_notification_view(self, request):
        if request.method == "POST":
            form = SystemNotificationForm(request.POST)
            if form.is_valid():
                NotificationService.create_system_notification(
                    title=form.cleaned_data["title"],
                    message=form.cleaned_data["message"],
                )
                self.message_user(request, "System notification sent successfully.")
                return redirect("admin:notifications_notification_changelist")
        else:
            form = SystemNotificationForm()

        context = {
            "form": form,
            "title": "Send System Notification",
        }
        return render(request, "admin/send_system_notification.html", context)


admin.site.register(Notification, NotificationAdmin)
