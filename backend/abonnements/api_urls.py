from django.urls import path

from . import api_views

urlpatterns = [
    path('mon-abonnement/', api_views.MonAbonnementAPIView.as_view(), name='api_mon_abonnement'),
    path('souscrire/', api_views.SouscrireAbonnementAPIView.as_view(), name='api_souscrire_abonnement'),
    path('annuler/', api_views.AnnulerAbonnementAPIView.as_view(), name='api_annuler_abonnement'),
]
