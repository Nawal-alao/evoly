"""
Nouveau fichier / mise à jour : abonnements/admin.py
============================================================================
Espace de gestion interne des abonnements. Pensé pour ton usage réel du
pilote école : activer d'un coup les abonnements de tous les élèves
d'un établissement qui vient de payer, sans avoir à cliquer élève par
élève.
"""

from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import Abonnement


@admin.action(description="Activer les abonnements sélectionnés")
def activer_abonnements(modeladmin, request, queryset):
    nombre = queryset.update(statut=Abonnement.Statut.ACTIF)
    modeladmin.message_user(request, f"{nombre} abonnement(s) activé(s).")


@admin.action(description="Marquer comme expiré")
def expirer_abonnements(modeladmin, request, queryset):
    nombre = queryset.update(statut=Abonnement.Statut.EXPIRE)
    modeladmin.message_user(request, f"{nombre} abonnement(s) marqué(s) comme expiré(s).")


@admin.action(description="Annuler les abonnements sélectionnés")
def annuler_abonnements(modeladmin, request, queryset):
    nombre = queryset.update(statut=Abonnement.Statut.ANNULE)
    modeladmin.message_user(request, f"{nombre} abonnement(s) annulé(s).")


@admin.action(description="Prolonger de 30 jours")
def prolonger_abonnements(modeladmin, request, queryset):
    for abonnement in queryset:
        abonnement.date_fin = abonnement.date_fin + timedelta(days=30)
        abonnement.save()
    modeladmin.message_user(request, f"{queryset.count()} abonnement(s) prolongé(s) de 30 jours.")


@admin.register(Abonnement)
class AbonnementAdmin(ModelAdmin):
    list_display = ("eleve", "formule", "statut", "date_debut", "date_fin")
    list_filter = ("statut", "formule")
    search_fields = ("eleve__prenom", "eleve__nom")
    date_hierarchy = "date_debut"
    actions = [activer_abonnements, expirer_abonnements, annuler_abonnements, prolonger_abonnements]

    # Astuce pratique pour le pilote : quand tu ajoutes un abonnement à la
    # main pour un élève, la date de fin par défaut est calculée automatiquement
    # à 30 jours (formule mensuelle), tu n'as qu'à l'ajuster si besoin.
    # IMPORTANT : date_fin est un DateTimeField, donc on retourne bien un
    # datetime timezone-aware (via timezone.now()), jamais juste .date().
    def get_changeform_initial_data(self, request):
        return {"date_fin": timezone.now() + timedelta(days=30)}