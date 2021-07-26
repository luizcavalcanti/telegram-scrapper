from django.contrib import admin
from django.urls import path

# TODO utilizar django-public-admin

urlpatterns = [path("admin/", admin.site.urls)]
