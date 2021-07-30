from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from telegram_scrapper.core.public_admin import public_admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", public_admin.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
