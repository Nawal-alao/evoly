from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline
from .models import Progression, Examen, Question, Resultat, ReponseEleve, ExerciceGroupe
 
@admin.action(description="Recalculer la progression sélectionnée")
def recalculer_progression(modeladmin, request, queryset):
    for progression in queryset:
        progression.recalculer()
 
 
@admin.register(Progression)
class ProgressionAdmin(ModelAdmin):
    list_display = ("eleve", "matiere", "niveau_maitrise", "derniere_mise_a_jour")
    list_filter = ("matiere",)
    actions = [recalculer_progression]


class QuestionInline(StackedInline):
    """
    Permet de relire, corriger, et valider chaque question générée
    directement depuis la page de l'Examen, sans naviguer ailleurs.
    """
    model = Question
    extra = 0  # ne pas proposer de ligne vide en plus des questions déjà générées
    fields = ("enonce", "groupe", "ordre_dans_groupe", "type_question", "notion", "choix_reponses", "bonne_reponse")


class ExerciceGroupeInline(StackedInline):
    model = ExerciceGroupe
    extra = 0
    fields = ("ordre", "enonce_principal")


@admin.register(Examen)
class ExamenAdmin(ModelAdmin):
    list_display = ("titre", "cours", "type_generation", "statut_validation", "date_publication")
    list_filter = ("statut_validation", "type_generation", "cours__matiere")
    inlines = [ExerciceGroupeInline, QuestionInline]
 
    def save_model(self, request, obj, form, change):
        # Si l'admin fait passer le statut à VALIDE manuellement dans le
        # formulaire, on trace qui a validé et quand — même logique que
        # pour Cours.professeur_validateur / date_validation.
        if obj.statut_validation == Examen.StatutValidation.VALIDE and not obj.date_validation:
            from django.utils import timezone
            obj.professeur_validateur = request.user
            obj.date_validation = timezone.now()
        super().save_model(request, obj, form, change)
 
 
@admin.register(Resultat)
class ResultatAdmin(ModelAdmin):
    list_display = ("eleve", "examen", "note", "date_passage")
    list_filter = ("examen",)
 