from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import EmailVerificationToken, User
from .models.profile_models import Skill, UserProfile, UserSkill


class UserSkillInline(admin.TabularInline):
    """Inline admin for user skills"""

    model = UserSkill
    extra = 1
    autocomplete_fields = ["skill"]


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profile"""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model"""

    list_display = ("email", "is_staff", "is_active", "email_verified")
    list_filter = ("is_staff", "is_active", "email_verified")
    search_fields = ("email",)
    ordering = ("email",)
    inlines = [UserProfileInline]

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


class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model"""

    list_display = ("user", "first_name", "last_name", "role", "experience_level")
    list_filter = ("role", "experience_level")
    search_fields = ("user__email", "first_name", "last_name")
    inlines = [UserSkillInline]
    fieldsets = (
        (_("User"), {"fields": ("user",)}),
        (
            _("Personal Info"),
            {"fields": ("first_name", "last_name", "profile_picture")},
        ),
        (_("Professional Info"), {"fields": ("role", "experience_level", "bio")}),
        (_("Links"), {"fields": ("portfolio_link", "github_link", "linkedin_link")}),
    )


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'role')
    list_filter = ('role',)
    search_fields = ('name',)
    ordering = ('role', 'name')


class UserSkillAdmin(admin.ModelAdmin):
    """Admin configuration for UserSkill model"""

    list_display = ("profile", "skill")
    list_filter = ("skill",)
    search_fields = ("profile__user__email", "skill__name")
    autocomplete_fields = ["profile", "skill"]


class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin configuration for EmailVerificationToken model"""

    list_display = ("user", "token", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("token",)


# Register models with admin site
admin.site.register(User, UserAdmin)
admin.site.register(EmailVerificationToken, EmailVerificationTokenAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(UserSkill, UserSkillAdmin)
