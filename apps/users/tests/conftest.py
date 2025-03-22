import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from .factories import UserFactory, VerifiedUserFactory, EmailVerificationTokenFactory


@pytest.fixture
def api_client():
    """Return an API client"""
    return APIClient()


@pytest.fixture
def user():
    """Return a user with unverified email"""
    return UserFactory()


@pytest.fixture
def verified_user():
    """Return a user with verified email"""
    return VerifiedUserFactory()


@pytest.fixture
def verification_token(user):
    """Return an email verification token"""
    return EmailVerificationTokenFactory(user=user)


@pytest.fixture
def auth_client(verified_user):
    """Return an authenticated API client"""
    client = APIClient()
    url = reverse('users:login')
    response = client.post(url, {
        'email': verified_user.email,
        'password': 'password123'
    }, format='json')
    
    token = response.data['data']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client