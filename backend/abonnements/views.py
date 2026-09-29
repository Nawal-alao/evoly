from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, View

from .models import Abonnement


class MonAbonnementView(LoginRequiredMixin, TemplateView):
    template_name = "abonnements/mon_abonnement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        eleve = self.request.user.profil_eleve
        context["abonnement_actif"] = eleve.abonnements.filter(statut="ACTIF").first()
        context["historique"] = eleve.abonnements.exclude(statut="ACTIF")
        return context

class SouscrireAbonnementView(LoginRequiredMixin, CreateView):
    model = Abonnement
    fields = ["formule", "date_fin"]
    template_name = "abonnements/souscrire.html"
    success_url = reverse_lazy("abonnements:mon_abonnement")

    def form_valid(self, form):
        form.instance.eleve = self.request.user.profil_eleve
        return super().form_valid(form)


class AnnulerAbonnementView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        eleve = request.user.profil_eleve
        abonnement = get_object_or_404(Abonnement, eleve=eleve, statut="ACTIF")
        abonnement.statut = "ANNULE"
        abonnement.save()
        return redirect("abonnements:mon_abonnement")