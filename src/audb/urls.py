from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r"", admin.site.urls),
    url(r"^google-auth/", include("google_auth.urls", namespace="google-auth")),
    url(r"^api/", include("core.urls")),
    url(r"^test-examples/", include("example_tests.urls")),
]
