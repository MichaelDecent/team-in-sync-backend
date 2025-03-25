from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.utils.api_response import APIResponse

from ..models.profile_models import Skill, UserSkill
from ..serializers.profile_serializers import (
    SkillSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSkillCreateSerializer,
)


@extend_schema(tags=["Profile"])
class UserProfileView(APIView):
    """View for managing user profile"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        """Get authenticated user's profile"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return APIResponse.success(data=serializer.data)

    @extend_schema(responses=UserProfileSerializer, request=UserProfileUpdateSerializer)
    def patch(self, request):
        """Update authenticated user's profile"""
        profile = request.user.profile
        serializer = UserProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            updated_profile = UserProfileSerializer(profile)
            return APIResponse.success(
                data=updated_profile.data, message="Profile updated successfully"
            )

        return APIResponse.bad_request(serializer.errors)


@extend_schema(tags=["Profile"])
class UserSkillView(APIView):
    """View for managing user skills"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SkillSerializer(many=True))
    def get(self, request):
        """Get list of all available skills"""
        skills = Skill.objects.all().order_by("name")
        serializer = SkillSerializer(skills, many=True)
        return APIResponse.success(data=serializer.data)

    @extend_schema(
        responses=UserSkillCreateSerializer, request=UserSkillCreateSerializer
    )
    def post(self, request):
        """Add a skill to user's profile"""
        serializer = UserSkillCreateSerializer(
            data=request.data, context={"profile": request.user.profile}
        )

        if serializer.is_valid():
            user_skill = serializer.save()
            return APIResponse.success(
                data={"id": user_skill.id, "skill": user_skill.skill.id},
                message="Skill added successfully",
            )

        return APIResponse.bad_request(serializer.errors)

    def delete(self, request, skill_id):
        """Remove a skill from user's profile"""
        try:
            skill = UserSkill.objects.get(profile=request.user.profile, id=skill_id)
            skill.delete()
            return APIResponse.success(message="Skill removed successfully")
        except UserSkill.DoesNotExist:
            return APIResponse.not_found("Skill not found")
