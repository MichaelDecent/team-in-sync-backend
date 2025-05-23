from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

API_V1 = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"{API_V1}schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{API_V1}docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(f"{API_V1}users/", include("apps.users.urls")),
    path(f"{API_V1}projects/", include("apps.projects.urls")),
    path(f"{API_V1}notifications/", include(("apps.notifications.urls", "notifications"))),
]
