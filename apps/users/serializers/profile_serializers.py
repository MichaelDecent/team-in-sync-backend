from rest_framework import serializers

from ..models.profile_models import Role, Skill, UserProfile, UserSkill


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""

    class Meta:
        model = Role
        fields = ("id", "name")
        read_only_fields = ("id",)


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
        fields = ("id", "skill_details")
        read_only_fields = ("id",)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user profile data"""

    profile_picture_url = serializers.SerializerMethodField()
    skills = UserSkillSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = RoleSerializer(read_only=True)

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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile data"""

    profile_picture = serializers.ImageField(required=False)
    full_name = serializers.CharField(required=False)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    role_name = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
            "profile_picture",
            "role_name",
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

    def validate(self, data):
        """Validate that either role or role_name is provided"""
        role_name = data.get("role_name")

        if not isinstance(role_name, str):
            raise serializers.ValidationError(
                {"role_name": "Role name must be a string."}
            )

        if role_name:
            try:
                role_obj = Role.objects.get(name=role_name)
                data["role"] = role_obj
            except Role.DoesNotExist:
                role_obj = Role.objects.create(name=role_name)
                data["role"] = role_obj

            data.pop("role_name", None)

        return data

    def update(self, instance, validated_data):
        """Update the user profile with validated data"""
        if "full_name" in validated_data:
            validated_data.pop("full_name")
            instance.first_name = getattr(self, "first_name", instance.first_name)
            instance.last_name = getattr(self, "last_name", instance.last_name)

        skill_names = validated_data.pop("skills", None)

        profile = super().update(instance, validated_data)

        if skill_names is not None:
            UserSkill.objects.filter(profile=profile).delete()

            processed_skills = []
            for skill_item in skill_names:
                if "," in skill_item:
                    split_skills = [s.strip() for s in skill_item.split(",")]
                    processed_skills.extend(split_skills)
                else:
                    processed_skills.append(skill_item.strip())

            for skill_name in processed_skills:
                if skill_name:
                    skill, created = Skill.objects.get_or_create(name=skill_name)
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

        if UserSkill.objects.filter(profile=profile, skill=skill).exists():
            raise serializers.ValidationError({"error": "You already have this skill"})

        user_skill = UserSkill.objects.create(profile=profile, skill=skill)
        return user_skill
