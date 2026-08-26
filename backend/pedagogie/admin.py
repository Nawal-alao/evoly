"""
pedagogie/admin.py — version complète et consolidée
============================================================================
Remplace entièrement ton fichier actuel par celui-ci. Réunit tout ce
qu'on a construit ensemble sur cette app :
- Matiere (avec coefficients par série en ligne)
- Cours (avec ses Séquences en ligne, et la génération d'examens par IA
  en 3 niveaux de difficulté)
"""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from .models import Matiere, CoefficientMatiere, Cours, Sequence, CoursProgression
from evaluations.services import generer_examen_ia


# ---------------------------------------------------------------------------
# MATIÈRE
# ---------------------------------------------------------------------------

class CoefficientMatiereInline(TabularInline):
    model = CoefficientMatiere
    extra = 1


@admin.register(Matiere)
class MatiereAdmin(ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)
    inlines = [CoefficientMatiereInline]


# ---------------------------------------------------------------------------
# COURS + SÉQUENCES
# ---------------------------------------------------------------------------

class SequenceInline(StackedInline):
    model = Sequence
    extra = 1
    ordering = ["ordre"]


def _generer_examen_niveau(niveau_difficulte, libelle):
    """Fabrique une action admin de génération d'examen pour un niveau donné."""
    def action(modeladmin, request, queryset):
        for cours in queryset:
            try:
                examen = generer_examen_ia(
                    cours, nombre_questions=5, niveau_difficulte=niveau_difficulte
                )
                messages.success(
                    request,
                    f"Examen {libelle} généré pour « {cours.titre} » "
                    f"({examen.questions.count()} questions). En attente de validation.",
                )
            except Exception as erreur:
                messages.error(request, f"Échec pour « {cours.titre} » : {erreur}")

    action.__name__ = f"generer_examen_{niveau_difficulte.lower()}"
    action.short_description = f"Générer un examen {libelle} via IA (Cohere)"
    return admin.action(description=action.short_description)(action)


generer_examen_facile = _generer_examen_niveau("FACILE", "Facile")
generer_examen_moyen = _generer_examen_niveau("MOYEN", "Moyen")
generer_examen_difficile = _generer_examen_niveau("DIFFICILE", "Difficile")


@admin.register(Cours)
class CoursAdmin(ModelAdmin):
    list_display = ("titre", "matiere", "classe_scolaire", "serie", "statut_validation")
    list_filter = ("statut_validation", "classe_scolaire", "serie", "matiere")
    search_fields = ("titre",)
    inlines = [SequenceInline]
    actions = [generer_examen_facile, generer_examen_moyen, generer_examen_difficile]


@admin.register(CoursProgression)
class CoursProgressionAdmin(ModelAdmin):
    list_display = ("eleve", "cours", "derniere_sequence", "date_mise_a_jour")
    list_filter = ("cours__matiere", "cours__classe_scolaire")
    search_fields = ("eleve__prenom", "eleve__nom", "cours__titre")