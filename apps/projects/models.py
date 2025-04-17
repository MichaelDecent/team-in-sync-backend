from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models.profile_models import Role, Skill


class Project(models.Model):
    """Model for projects that users can create and collaborate on"""

    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("on_hold", _("On Hold")),
        ("cancelled", _("Cancelled")),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="owned_projects"
    )
    team_members = models.ManyToManyField(
        "users.User",
        through="ProjectMembership",
        related_name="projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectRole(models.Model):
    """Model for defining roles needed for a project"""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="required_roles"
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="roles", null=True, blank=True
    )
    custom_role_name = models.CharField(max_length=100, null=True, blank=True)
    number_required = models.PositiveIntegerField(default=1)

    def __str__(self):
        role_name = self.get_role_display
        return f"{self.project.title} - {role_name}"

    class Meta:
        # Change unique constraint to accommodate either role or custom_role_name
        constraints = [
            models.UniqueConstraint(
                fields=["project", "role"],
                condition=models.Q(role__isnull=False),
                name="unique_project_predefined_role",
            ),
            models.UniqueConstraint(
                fields=["project", "custom_role_name"],
                condition=models.Q(custom_role_name__isnull=False),
                name="unique_project_custom_role",
            ),
        ]

    @property
    def get_role_display(self):
        """Return the display name of the role (predefined or custom)"""
        return self.role.name if self.role else self.custom_role_name


class ProjectRoleSkill(models.Model):
    """Model for defining skills needed for a specific project role"""

    project_role = models.ForeignKey(
        ProjectRole, on_delete=models.CASCADE, related_name="required_skills"
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="project_roles",
        null=True,
        blank=True,
    )
    custom_skill_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        skill_name = self.skill.name if self.skill else self.custom_skill_name
        return f"{self.project_role} - {skill_name}"

    class Meta:
        # Change unique constraint to accommodate either skill or custom_skill_name
        constraints = [
            models.UniqueConstraint(
                fields=["project_role", "skill"],
                condition=models.Q(skill__isnull=False),
                name="unique_project_role_predefined_skill",
            ),
            models.UniqueConstraint(
                fields=["project_role", "custom_skill_name"],
                condition=models.Q(custom_skill_name__isnull=False),
                name="unique_project_role_custom_skill",
            ),
        ]


class ProjectMembership(models.Model):
    """Model for managing user membership in projects"""

    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    )

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.ForeignKey(
        ProjectRole, on_delete=models.CASCADE, related_name="memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.user.email} - {self.project.title} - {self.role.get_role_display}"

    class Meta:
        unique_together = ("user", "project", "role")
