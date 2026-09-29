from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from pedagogie.models import Matiere

from .models import Eleve, Mentor, SuiviMentor


class InscriptionEleveView(CreateView):
    model = Eleve
    fields = ["prenom", "nom", "age", "classe_scolaire", "serie"]
    template_name = "comptes/inscription_eleve.html"
    success_url = reverse_lazy("comptes:connexion")

    def form_valid(self, form):
        username = self.request.POST.get("username")

        if User.objects.filter(username=username).exists():
            form.add_error(None, "Ce nom d'utilisateur est déjà pris. Choisis-en un autre.")
            return self.form_invalid(form)

        user = User.objects.create_user(
            username=username,
            password=self.request.POST.get("password"),
        )
        form.instance.utilisateur = user
        return super().form_valid(form)


class InscriptionMentorView(CreateView):
    model = Mentor
    fields = ["prenom", "nom", "bio", "matieres"]
    template_name = "comptes/inscription_mentor.html"
    success_url = reverse_lazy("comptes:connexion")  # à adapter selon ton urls.py

    def form_valid(self, form):
        # Étape 1 : créer le User d'abord (Django gère le hachage du mot de passe)
        user = User.objects.create_user(
            username=self.request.POST.get("username"),
            password=self.request.POST.get("password"),
        )
        # Étape 2 : lier ce User au Mentor en cours de création, avant sauvegarde
        form.instance.utilisateur = user

        # Étape 3 : laisser Django terminer (sauvegarde + redirection)
        return super().form_valid(form)

class ConnexionView(LoginView):
    template_name = "comptes/connexion.html"

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, "profil_eleve"):
            return reverse_lazy("dashboard:dashboard_eleve")
        elif hasattr(user, "profil_mentor"):
            return reverse_lazy("dashboard:dashboard_mentor")
        return reverse_lazy("dashboard:accueil")  # sécurité si aucun profil trouvé

class DeconnexionView(LogoutView):
    next_page = "dashboard:accueil"


class ListeMentorsView(LoginRequiredMixin, ListView):
    model = Mentor
    template_name = "comptes/liste_mentors.html"
    context_object_name = "mentors"

    def get_queryset(self):
        queryset = Mentor.objects.filter(disponible=True).prefetch_related("matieres")
        matiere_id = self.request.GET.get("matiere")
        if matiere_id:
            queryset = queryset.filter(matieres__id=matiere_id)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matieres"] = Matiere.objects.all()
        context["matiere_selectionnee"] = self.request.GET.get("matiere", "")
        return context


class SuivreMentorView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        eleve = request.user.profil_eleve
        mentor = get_object_or_404(Mentor, pk=kwargs["pk"])
        matiere_id = request.POST.get("matiere")
        matiere = get_object_or_404(Matiere, pk=matiere_id)

        # Garde-fou métier : le mentorat nécessite un abonnement actif,
        # contrairement aux cours qui restent accessibles via la licence école.
        abonnement_actif = eleve.abonnements.filter(statut="ACTIF").exists()
        if not abonnement_actif:
            messages.warning(
                request,
                "Un abonnement actif est nécessaire pour suivre un mentor.",
            )
            return redirect("abonnements:souscrire")

        _suivi, cree = SuiviMentor.objects.get_or_create(
            eleve=eleve, mentor=mentor, matiere=matiere,
        )

        if cree:
            messages.success(request, f"Tu suis maintenant {mentor.prenom} en {matiere.nom}.")
        else:
            messages.info(request, "Tu suis déjà ce mentor dans cette matière.")

        return redirect("comptes:liste_mentors")


class ProfilEleveView(LoginRequiredMixin, UpdateView):
    model = None  # défini dynamiquement dans get_object, voir ci-dessous
    fields = ["prenom", "nom", "age", "classe_scolaire", "serie"]
    template_name = "comptes/profil_eleve.html"
    success_url = reverse_lazy("comptes:profil_eleve")

    def get_object(self, queryset=None):
        # Toujours le profil de l'utilisateur connecté, jamais un pk arbitraire
        # dans l'URL — élimine tout risque d'IDOR par construction.
        return self.request.user.profil_eleve

    def form_valid(self, form):
        messages.success(self.request, "Ton profil a été mis à jour.")
        return super().form_valid(form)


class ProfilMentorView(LoginRequiredMixin, UpdateView):
    model = None
    fields = ["prenom", "nom", "bio", "matieres", "disponible"]
    template_name = "comptes/profil_mentor.html"
    success_url = reverse_lazy("comptes:profil_mentor")

    def get_object(self, queryset=None):
        return self.request.user.profil_mentor

    def form_valid(self, form):
        messages.success(self.request, "Ton profil a été mis à jour.")
        return super().form_valid(form)


class NoterMentorView(LoginRequiredMixin, View):
 
    def post(self, request, *args, **kwargs):
        eleve = request.user.profil_eleve
        suivi = get_object_or_404(SuiviMentor, pk=kwargs["pk"], eleve=eleve)
 
        try:
            note = int(request.POST.get("note", ""))
        except ValueError:
            note = None
 
        if note is None or not (1 <= note <= 5):
            messages.error(request, "Merci de donner une note entre 1 et 5.")
        else:
            suivi.note_evaluation = note
            suivi.save()
            messages.success(request, f"Tu as noté {suivi.mentor.prenom} {note}/5.")
 
        return redirect("dashboard:dashboard_eleve")