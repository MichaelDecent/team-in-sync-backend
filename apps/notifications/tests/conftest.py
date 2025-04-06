import pytest
from rest_framework.test import APIClient

from apps.notifications.models import Notification, NotificationType
from apps.projects.models import Project, ProjectMembership
from apps.users.tests.factories import VerifiedUserFactory


@pytest.fixture
def user():
    """Return a verified user"""
    return VerifiedUserFactory()


@pytest.fixture
def notification(user):
    """Return a notification"""
    return Notification.objects.create(
        recipient=user,
        type=NotificationType.SYSTEM_UPDATE,
        title="Test Notification",
        message="This is a test notification",
        read=False,
    )


@pytest.fixture
def owner():
    """Return a project owner"""
    return VerifiedUserFactory()


@pytest.fixture
def requester():
    """Return a user requesting to join a project"""
    return VerifiedUserFactory()


@pytest.fixture
def project(owner):
    """Return a project"""
    return Project.objects.create(
        title="Test Project",
        description="A test project description",
        owner=owner,
        status="pending",
    )


@pytest.fixture
def membership(project, requester):
    """Return a project membership (join request)"""
    return ProjectMembership.objects.create(
        project=project,
        user=requester,
        role="designer",
        status="pending",
    )


@pytest.fixture
def another_user():
    """Return another verified user"""
    return VerifiedUserFactory()


@pytest.fixture
def auth_client(user):
    """Return an authenticated API client"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def user_notification(user):
    """Return a notification for the test user"""
    return Notification.objects.create(
        recipient=user,
        type=NotificationType.SYSTEM_UPDATE,
        title="User Notification",
        message="This is a notification for the test user",
    )


@pytest.fixture
def other_user_notification(another_user):
    """Return a notification for another user"""
    return Notification.objects.create(
        recipient=another_user,
        type=NotificationType.SYSTEM_UPDATE,
        title="Other User Notification",
        message="This is a notification for another user",
    )
