from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdmin(BaseUserAdmin):
    # Make sure first_name and last_name are NOT in list_display
    list_display = ("email", "is_staff", "is_active", "email_verified")
    list_filter = ("is_staff", "is_active", "email_verified")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "email_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "email_verified",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(User, UserAdmin)
