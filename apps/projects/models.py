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
    number_required = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "role"],
                name="unique_project_role",
            ),
        ]

    def __str__(self):
        if hasattr(self, "role") and self.role:
            return f"{self.project.title} - {self.role.name}"
        return f"{self.project.title} - Unknown Role"


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

    def __str__(self):
        return f"{self.project_role} - {self.skill.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project_role", "skill"],
                name="unique_project_role_skill",
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
        role_name = self.role.role.name if self.role and self.role.role else "Unknown Role"
        return f"{self.user.email} - {self.project.title} - {role_name}"

    class Meta:
        unique_together = ("user", "project", "role")
