from rest_framework import serializers

from ..models.profile_models import Skill, UserProfile, UserSkill


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model"""

    class Meta:
        model = Skill
        fields = ("id", "name")
        read_only_fields = ("id",)


class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for UserSkill model"""

    skill_details = SkillSerializer(source="skill", read_only=True)

    class Meta:
        model = UserSkill
        fields = ("id", "skill", "skill_details")
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
            "first_name",
            "last_name",
            "full_name",
            "profile_picture",
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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile data"""
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "last_name",
            "profile_picture",
            "role",
            "experience_level",
            "portfolio_link",
            "github_link",
            "linkedin_link",
            "bio",
        )


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
