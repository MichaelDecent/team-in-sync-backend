import uuid

import factory
from django.contrib.auth import get_user_model

from apps.users.models import EmailVerificationToken

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test User instances"""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    is_active = True
    email_verified = False


class VerifiedUserFactory(UserFactory):
    """Factory for creating test User instances with verified email"""

    email_verified = True


class EmailVerificationTokenFactory(factory.django.DjangoModelFactory):
    """Factory for creating test EmailVerificationToken instances"""

    class Meta:
        model = EmailVerificationToken

    user = factory.SubFactory(UserFactory)
    token = factory.LazyFunction(uuid.uuid4)
