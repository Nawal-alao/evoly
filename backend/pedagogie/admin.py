"""
pedagogie/admin.py — version complète et consolidée
============================================================================
Remplace entièrement ton fichier actuel par celui-ci. Réunit tout ce
qu'on a construit ensemble sur cette app :
- Matiere (avec coefficients par série en ligne)
- Cours (avec ses Séquences en ligne, et la génération d'examens par IA)
"""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from evaluations.services import generer_examen_ia

from .models import CoefficientMatiere, Cours, CoursProgression, Matiere, Sequence

# ---------------------------------------------------------------------------
# MATIÈRE
# ---------------------------------------------------------------------------

class CoefficientMatiereInline(TabularInline):
    model = CoefficientMatiere
    extra = 1


@admin.register(Matiere)
class MatiereAdmin(ModelAdmin):
    list_display = ("nom", "editeur_math_actif")
    list_editable = ("editeur_math_actif",)
    search_fields = ("nom",)
    inlines = [CoefficientMatiereInline]


# ---------------------------------------------------------------------------
# COURS + SÉQUENCES
# ---------------------------------------------------------------------------

class SequenceInline(StackedInline):
    model = Sequence
    extra = 1
    ordering = ["ordre"]


def generer_examen_ia_action(modeladmin, request, queryset):
    for cours in queryset:
        try:
            examen = generer_examen_ia(cours, nombre_questions=5)
            messages.success(
                request,
                f"Examen généré pour « {cours.titre} » "
                f"({examen.questions.count()} questions). En attente de validation.",
            )
        except Exception as erreur:
            messages.error(request, f"Échec pour « {cours.titre} » : {erreur}")

generer_examen_ia_action.__name__ = "generer_examen_ia_action"
generer_examen_ia_action.short_description = "Générer un examen via IA (Cohere)"


@admin.register(Cours)
class CoursAdmin(ModelAdmin):
    list_display = ("titre", "matiere", "classe_scolaire", "serie", "statut_validation")
    list_filter = ("statut_validation", "classe_scolaire", "serie", "matiere")
    search_fields = ("titre",)
    inlines = [SequenceInline]
    actions = [generer_examen_ia_action]


@admin.register(CoursProgression)
class CoursProgressionAdmin(ModelAdmin):
    list_display = ("eleve", "cours", "derniere_sequence", "date_mise_a_jour")
    list_filter = ("cours__matiere", "cours__classe_scolaire")
    search_fields = ("eleve__prenom", "eleve__nom", "cours__titre")