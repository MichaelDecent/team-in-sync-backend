from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.utils.api_response import APIResponse
from core.utils.tokens import get_tokens_for_user

from ..models.profile_models import Role, Skill, UserProfile, UserSkill
from ..serializers.profile_serializers import (
    RoleSerializer,
    SkillSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSkillCreateSerializer,
    UserSkillSerializer,
)


@extend_schema(tags=["Profile"])
class UserProfileView(APIView):
    """View for managing user profile"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        """Get authenticated user's profile"""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return APIResponse.not_found("Profile not found")
        serializer = UserProfileSerializer(profile)
        return APIResponse.success(data=serializer.data)

    @extend_schema(responses=UserProfileSerializer, request=UserProfileUpdateSerializer)
    def patch(self, request):
        """Update authenticated user's profile"""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return APIResponse.not_found("Profile not found")

        serializer = UserProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # Refresh the profile instance to ensure we have latest data
            profile.refresh_from_db()

            updated_profile = UserProfileSerializer(profile).data

            updated_profile["tokens"] = get_tokens_for_user(request.user)

            updated_profile["is_profile_complete"] = profile.is_complete()

            return APIResponse.success(
                data=updated_profile, message="Profile updated successfully"
            )

        return APIResponse.bad_request(serializer.errors)


@extend_schema(tags=["Profile"])
class UserSkillView(APIView):
    """View for managing user skills"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SkillSerializer(many=True))
    def get(self, request):
        """Get list of all available skills, optionally filtered by role"""
        skills_query = UserSkill.objects.all().filter(profile=request.user.profile)

        role = request.query_params.get("role")
        if role:
            skills_query = skills_query.filter(role=role)

        serializer = UserSkillSerializer(skills_query, many=True)
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


@extend_schema(tags=["Skills"])
class SkillView(APIView):
    """View to get all available skills based on role"""

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        responses=SkillSerializer(many=True),
        parameters=[
            OpenApiParameter(
                name="role",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter skills by role",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search skills by name",
                required=False,
            ),
        ],
    )
    def get(self, request):
        """Get all skills with optional filtering"""
        skills = Skill.objects.all().order_by("name")

        # Filter by role if provided
        role = request.query_params.get("role")
        if role:
            skills = skills.filter(role=role)

        # Search by name if provided
        search = request.query_params.get("search")
        if search:
            skills = skills.filter(name__icontains=search)

        serializer = SkillSerializer(skills, many=True)
        return APIResponse.success(data=serializer.data)


@extend_schema(tags=["Roles"])
class RoleView(APIView):
    """View for managing roles"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=RoleSerializer(many=True))
    def get(self, request):
        """Get list of all available roles"""
        roles = Role.objects.all().order_by("name")

        serializer = RoleSerializer(roles, many=True)
        return APIResponse.success(data=serializer.data)
