"""
URL configuration for asset_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
# ------------------------------------------------------------------
# Custom logout view
# ------------------------------------------------------------------
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    Log the user out and redirect to the login page.

    We provide our own implementation so that both GET and POST requests are
    accepted, eliminating the “405 Method Not Allowed” error users were seeing
    when hitting `/accounts/logout/` via GET.
    """
    django_logout(request)
    return redirect("login")

urlpatterns = [
    path("admin/", admin.site.urls),

    # App URLS
    path("assets/", include("assets.urls")),
    path("incidents/", include("incidents.urls")),

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    # Custom logout accepting both GET & POST and covering both routes
    path("logout/", logout_view, name="logout"),
    path("accounts/logout/", logout_view),  # override built-in pattern

    # Django authentication (login, logout, password reset, etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # Redirect root URL to assets dashboard
    path(
        "",
        RedirectView.as_view(pattern_name="asset_dashboard", permanent=False),
        name="root_redirect",
    ),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
