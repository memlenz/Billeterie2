from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("J7GuncjzSMsqWhSveaYRwg/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("management/verifiers/", include("accounts.urls_verifiers")),
    path("", include("pages.urls")),
    path("qrgenerator/", include("qrgenerator.urls", namespace="qrgenerator")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
