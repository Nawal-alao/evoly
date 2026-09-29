"""
URL configuration for Evoly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('dashboard.urls')),
    path('comptes/', include('comptes.urls')),
    path('abonnements/', include('abonnements.urls')),
    path('evaluations/', include('evaluations.urls')),
    path('pedagogie/', include('pedagogie.urls')),
    path('communaute/', include('communaute.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
