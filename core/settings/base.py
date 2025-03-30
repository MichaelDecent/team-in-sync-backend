from datetime import timedelta
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ALLOWED_HOSTS = getenv("ALLOWED_HOSTS", "127.0.0.1").split(",")

AUTH_USER_MODEL = "users.User"

APPEND_SLASH = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv("SECRET_KEY", "your-default-secret-key")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "cloudinary_storage",
    "cloudinary",
    "social_django",
    # Local apps
    "apps.users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "TEAM-IN-SYNC API",
    "DESCRIPTION": "API for TEAM-IN-SYNC Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.utils.exception_handler.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = getenv("EMAIL_PORT", 465)
EMAIL_USE_TLS = getenv("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = getenv("EMAIL_USE_SSL", True)
EMAIL_HOST_USER = getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")

FRONTEND_URL = getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = getenv("BACKEND_URL", "http://localhost:8000")

CORS_ALLOW_CREDENTIALS = True
# Security Headers
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Cloudinary configuration
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": getenv("CLOUDINARY_API_SECRET"),
}

# Configure default file storage
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"


# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(getenv("ACCESS_TOKEN_LIFETIME", "10"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(getenv("REFRESH_TOKEN_LIFETIME", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Social Auth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv("GOOGLE_OAUTH2_CLIENT_ID", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv("GOOGLE_OAUTH2_CLIENT_SECRET", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["email", "profile"]

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

# Configure the redirection URLs
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/api/v1/users/social/complete/"
SOCIAL_AUTH_LOGIN_ERROR_URL = "/api/v1/users/social/error/"
