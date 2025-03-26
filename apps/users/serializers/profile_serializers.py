from django.db.models.query import QuerySet
from rest_framework import serializers

from ..models.profile_models import Skill, UserProfile, UserSkill


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model"""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Skill
        fields = ("id", "name", "role", "role_display")
        read_only_fields = ("id",)


class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for UserSkill model"""

    skill_details = SkillSerializer(source="skill", read_only=True)

    class Meta:
        model = UserSkill
        fields = ("id", "skill_details")
        read_only_fields = ("id",)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user profile data"""

    profile_picture_url = serializers.SerializerMethodField()
    skills = UserSkillSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user",
            "full_name",
            "profile_picture_url",
            "role",
            "experience_level",
            "portfolio_link",
            "github_link",
            "linkedin_link",
            "bio",
            "skills",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_profile_picture_url(self, obj):
        """Get the URL of the profile picture if it exists"""
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


class SkillsField(serializers.PrimaryKeyRelatedField):
    """Custom field for handling skills in different input formats"""

    def to_internal_value(self, data):
        """
        Convert various input formats to list of Skill objects.
        Handles:
        - Single ID
        - List of IDs
        - Comma-separated string of IDs
        """
        # Print debugging to see what we're receiving
        print(f"Raw skills data: {data}")

        try:
            if data is None or data == "":
                return []

            if isinstance(data, str) and "," in data:
                ids = [int(id.strip()) for id in data.split(",") if id.strip()]
                return list(Skill.objects.filter(id__in=ids))

            if isinstance(data, list) and all(isinstance(item, Skill) for item in data):
                return data

            return super().to_internal_value(data)

        except Exception as e:
            print(f"Error processing skills data: {e}")
            raise serializers.ValidationError(f"Invalid skill data format: {data}")


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile data"""

    profile_picture = serializers.ImageField(required=False)
    full_name = serializers.CharField(required=False)
    skills = SkillsField(queryset=Skill.objects.all(), many=True, required=False)

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
            "profile_picture",
            "role",
            "experience_level",
            "portfolio_link",
            "github_link",
            "linkedin_link",
            "bio",
            "skills",
        )

    def validate_full_name(self, value):
        """Validate and split full name into first and last name components"""
        if not value:
            return value

        name_parts = value.split(maxsplit=1)
        if len(name_parts) == 1:
            self.first_name = name_parts[0]
            self.last_name = ""
        else:
            self.first_name = name_parts[0]
            self.last_name = name_parts[1]

        return value

    def validate_skills(self, skills):
        """Validate that skills are compatible with the selected role"""
        print(f"Skills: {skills}")
        new_role = self.initial_data.get("role", None)
        if new_role is None and self.instance:
            new_role = self.instance.role

        if new_role and skills:
            incompatible_skills = [s for s in skills if s.role != new_role]

            if incompatible_skills:
                skill_names = [s.name for s in incompatible_skills]
                raise serializers.ValidationError(
                    f"The following skills are not compatible with the selected role: {', '.join(skill_names)}"
                )

        return skills

    def update(self, instance, validated_data):
        """Update the user profile with validated data"""
        if "full_name" in validated_data:
            validated_data.pop("full_name")
            instance.first_name = getattr(self, "first_name", instance.first_name)
            instance.last_name = getattr(self, "last_name", instance.last_name)

        skills = validated_data.pop("skills", None)

        profile = super().update(instance, validated_data)

        if skills is not None:
            UserSkill.objects.filter(profile=profile).delete()

            flat_skills = []
            for item in skills:
                if isinstance(item, list) or isinstance(item, QuerySet):
                    for skill in item:
                        flat_skills.append(skill)
                else:
                    flat_skills.append(item)

            for skill in flat_skills:
                UserSkill.objects.create(profile=profile, skill=skill)

        return profile


class UserSkillCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding skills to a user profile"""

    class Meta:
        model = UserSkill
        fields = ("skill",)

    def create(self, validated_data):
        """Create a new UserSkill instance"""
        profile = self.context.get("profile")
        if not profile:
            raise serializers.ValidationError({"error": "Profile is required"})

        skill = validated_data.get("skill")

        # Check if the user already has this skill
        if UserSkill.objects.filter(profile=profile, skill=skill).exists():
            raise serializers.ValidationError({"error": "You already have this skill"})

        user_skill = UserSkill.objects.create(profile=profile, skill=skill)
        return user_skill
