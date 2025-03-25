from cloudinary.models import CloudinaryField
from django.db import models
from django.utils.translation import gettext_lazy as _


class RoleChoices(models.TextChoices):
    DEVELOPER = "developer", _("Developer")
    DESIGNER = "designer", _("Designer")
    PRODUCT_MANAGER = "product_manager", _("Product Manager")
    PROJECT_MANAGER = "project_manager", _("Project Manager")
    QA_ENGINEER = "qa_engineer", _("QA Engineer")
    DEVOPS_ENGINEER = "devops_engineer", _("DevOps Engineer")
    BUSINESS_ANALYST = "business_analyst", _("Business Analyst")
    OTHER = "other", _("Other")


class ExperienceLevelChoices(models.TextChoices):
    JUNIOR = "junior", _("Junior (0-2 years)")
    MID_LEVEL = "mid_level", _("Mid-Level (2-5 years)")
    SENIOR = "senior", _("Senior (5-8 years)")
    LEAD = "lead", _("Lead (8+ years)")
    PRINCIPAL = "principal", _("Principal/Architect")


class UserProfile(models.Model):
    """Extended user profile information"""

    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="profile"
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    profile_picture = CloudinaryField(
        "profile_pictures",
        folder="team_in_sync/profile_pictures",
        blank=True,
        null=True,
        transformation={"width": 300, "height": 300, "crop": "fill"},
    )
    role = models.CharField(
        max_length=30,
        choices=RoleChoices.choices,
        default=RoleChoices.DEVELOPER,
    )
    experience_level = models.CharField(
        max_length=30,
        choices=ExperienceLevelChoices.choices,
        default=ExperienceLevelChoices.JUNIOR,
    )
    portfolio_link = models.URLField(_("portfolio link"), blank=True)
    github_link = models.URLField(_("GitHub link"), blank=True)
    linkedin_link = models.URLField(_("LinkedIn link"), blank=True)
    bio = models.TextField(_("bio"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def full_name(self):
        """Return the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.user.email


class Skill(models.Model):
    """Model for skills that users can have"""

    name = models.CharField(_("name"), max_length=100, unique=True)

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Many-to-many relationship between users and skills"""

    profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="skills"
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("profile", "skill")
        verbose_name = _("user skill")
        verbose_name_plural = _("user skills")

    def __str__(self):
        return f"{self.profile.user.email} - {self.skill.name}"
