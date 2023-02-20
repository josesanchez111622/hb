"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls import url
from django.views.generic.base import RedirectView
import debug_toolbar
from pro import urls as pro_urls
from backend.core import urls as core_urls

urlpatterns = [
    path('', RedirectView.as_view(url='app/sadmin/')),
    path("app/sadmin/", admin.site.urls, name="admin"),
    path("api/booking/", include("booking.urls")),
    path('api/pro/', include(pro_urls)),
    path("", include(core_urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns = [
        url('app/__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
