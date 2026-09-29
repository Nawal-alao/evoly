from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .models import Examen, Progression, ReponseEleve, Resultat


class ListeExamensDisponiblesView(LoginRequiredMixin, ListView):
    model = Examen
    template_name = "evaluations/liste_examens.html"
    context_object_name = "examens_disponibles"
 
    def get_queryset(self):
        eleve = self.request.user.profil_eleve
        return Examen.objects.filter(
            cours__classe_scolaire=eleve.classe_scolaire,
            cours__serie=eleve.serie,
            cours__statut_validation="VALIDE",
            statut_validation="VALIDE",
            date_publication__lt=timezone.now(),
        ).select_related("cours", "cours__matiere").order_by(
            "niveau_difficulte", "-date_publication"  # NOUVEAU : tri requis pour {% regroup %}
        )


class ResultatExamenDetailView(LoginRequiredMixin, DetailView):
    model = Resultat
    template_name = "evaluations/resultat_examen.html"
    context_object_name = "resultat"

    def get_queryset(self):
        return Resultat.objects.filter(eleve=self.request.user.profil_eleve)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resultat = self.object
        context["reponses"] = ReponseEleve.objects.filter(
            eleve=resultat.eleve,
            question__examen=resultat.examen,
        ).select_related("question").order_by("question__id")
        return context


class PasserExamenView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        examen = get_object_or_404(Examen, pk=kwargs["pk"])
        questions = examen.questions.all()
        return render(request, "evaluations/passer_examen.html", {
            "examen": examen,
            "questions": questions,
        })

    def post(self, request, *args, **kwargs):
        examen = get_object_or_404(Examen, pk=kwargs["pk"])
        eleve = request.user.profil_eleve
        questions = examen.questions.all()

        # Repassage : on remplace la tentative précédente pour que les
        # réponses affichées et la progression reflètent la dernière.
        ReponseEleve.objects.filter(
            eleve=eleve, question__examen=examen,
        ).delete()

        nombre_correct = 0
        total_questions = questions.count()

        for question in questions:
            reponse_donnee = request.POST.get(f"reponse_{question.id}", "")
            correct = (reponse_donnee.strip() == question.bonne_reponse.strip())

            ReponseEleve.objects.create(
                eleve=eleve,
                question=question,
                reponse_donnee=reponse_donnee,
                correct=correct,
            )

            if correct:
                nombre_correct += 1

        progression, _ = Progression.objects.get_or_create(
            eleve=eleve, matiere=examen.cours.matiere
        )
        progression.recalculer()

        note = (nombre_correct / total_questions) * 20 if total_questions > 0 else 0

        Resultat.objects.update_or_create(
            eleve=eleve,
            examen=examen,
            defaults={
                "note": note,
                "date_passage": timezone.now(),
            },
        )

        return redirect("evaluations:resultat_examen", pk=examen.pk)