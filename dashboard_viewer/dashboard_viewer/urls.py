"""dashboard_viewer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .views import (
    bad_request,
    forbidden,
    not_found,
    production_media_files,
    server_error,
)

handler400 = bad_request
handler403 = forbidden
handler404 = not_found
handler500 = server_error

urlpatterns = [
    # path("", include("tabsManager.urls")),
    path("admin/", admin.site.urls),
    path("martor/", include("martor.urls")),
    path("uploader/", include("uploader.urls")),
    re_path(
        fr'^{re.escape(settings.MEDIA_URL.lstrip("/"))}(?P<path>.*)$',
        serve,
        kwargs={"document_root": settings.MEDIA_ROOT},
    )
    if settings.DEBUG
    else re_path(r"^media/(?P<path>.*)$", production_media_files),
]
