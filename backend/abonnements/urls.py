from django.urls import path

from .views import AnnulerAbonnementView, MonAbonnementView, SouscrireAbonnementView

app_name = "abonnements"

urlpatterns = [
    path("", MonAbonnementView.as_view(), name="mon_abonnement"),
    path("souscrire/", SouscrireAbonnementView.as_view(), name="souscrire"),
    path("annuler/", AnnulerAbonnementView.as_view(), name="annuler"),
]