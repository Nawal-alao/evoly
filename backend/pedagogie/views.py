from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import Cours


def _cours_de_lutilisateur(user):
    """
    Retourne les Cours accessibles à l'utilisateur connecté.
    - Élève : uniquement les cours validés de SA classe et SA série.
    - Mentor : accès libre à TOUS les cours validés, sans restriction.
    """
    if hasattr(user, "profil_eleve"):
        eleve = user.profil_eleve
        return Cours.objects.filter(
            classe_scolaire=eleve.classe_scolaire,
            serie=eleve.serie,
            statut_validation="VALIDE",
        )
    elif hasattr(user, "profil_mentor"):
        return Cours.objects.filter(statut_validation="VALIDE")
    return Cours.objects.none()
 
 
class ListeCoursView(LoginRequiredMixin, ListView):
    model = Cours
    template_name = "pedagogie/liste_cours.html"
    context_object_name = "cours_liste"
 
    def get_queryset(self):
        return _cours_de_lutilisateur(self.request.user)
 
 
class DetailCoursView(LoginRequiredMixin, DetailView):
    model = Cours
    template_name = "pedagogie/detail_cours.html"
    context_object_name = "cours"
 
    def get_queryset(self):
        return _cours_de_lutilisateur(self.request.user)
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sequences"] = self.object.sequences.all()
        return context
 