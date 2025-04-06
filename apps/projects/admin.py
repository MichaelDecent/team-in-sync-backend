from django.contrib import admin

from .models import Project, ProjectMembership, ProjectRole, ProjectRoleSkill


class ProjectRoleInline(admin.TabularInline):
    model = ProjectRole
    extra = 1


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    autocomplete_fields = ["user"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "owner__email")
    date_hierarchy = "created_at"
    inlines = [ProjectRoleInline, ProjectMembershipInline]
    autocomplete_fields = ["owner"]


class ProjectRoleSkillInline(admin.TabularInline):
    model = ProjectRoleSkill
    extra = 1
    autocomplete_fields = ["skill"]


@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    list_display = ("project", "role", "number_required")
    list_filter = ("role", "project")
    search_fields = ("project__title", "role")
    inlines = [ProjectRoleSkillInline]
    autocomplete_fields = ["project"]


@admin.register(ProjectRoleSkill)
class ProjectRoleSkillAdmin(admin.ModelAdmin):
    list_display = ("project_role", "skill")
    list_filter = ("skill", "project_role__project")
    search_fields = ("skill__name", "project_role__project__title")
    autocomplete_fields = ["project_role", "skill"]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role", "status", "joined_at")
    list_filter = ("status", "role", "joined_at")
    search_fields = ("user__email", "project__title")
    date_hierarchy = "joined_at"
    autocomplete_fields = ["user", "project"]
