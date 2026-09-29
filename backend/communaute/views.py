import string

from django.contrib import messages as django_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from comptes.models import SuiviMentor

from .models import GroupeEtude, Message, MessagePrive, MotInterdit, Signalement
from .services import contient_mot_interdit


def _groupes_de_lutilisateur(user):
    """
    Retourne les GroupeEtude validés pertinents pour l'utilisateur connecté,
    qu'il soit élève (filtré par classe/série) ou mentor (filtré par
    les matières qu'il enseigne). Exclut systématiquement les groupes
    EN_ATTENTE et REJETÉ — seuls les admins Django les voient.
    """
    base = GroupeEtude.objects.filter(statut_validation=GroupeEtude.StatutValidation.VALIDE)

    if hasattr(user, "profil_eleve"):
        eleve = user.profil_eleve
        return base.filter(
            classe_scolaire=eleve.classe_scolaire,
            serie=eleve.serie,
        )
    elif hasattr(user, "profil_mentor"):
        return base.filter(matiere__in=user.profil_mentor.matieres.all())
    return GroupeEtude.objects.none()
 
 
class ListeGroupesView(LoginRequiredMixin, ListView):
    model = GroupeEtude
    template_name = "communaute/liste_groupes.html"
    context_object_name = "groupes"
 
    def get_queryset(self):
        return _groupes_de_lutilisateur(self.request.user).select_related("matiere").order_by(
            "matiere__nom", "nom"
        )


class DetailGroupeView(LoginRequiredMixin, DetailView):
    model = GroupeEtude
    template_name = "communaute/detail_groupe.html"
    context_object_name = "groupe"
 
    def get_queryset(self):
        # Sécurité : même principe qu'avant, mais couvre maintenant les deux profils.
        return _groupes_de_lutilisateur(self.request.user)
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages_groupe"] = self.object.messages.filter(
            statut=Message.Statut.VISIBLE,
        ).select_related("auteur").order_by("date_envoi")
        return context

class EnvoyerMessageView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        groupe = get_object_or_404(GroupeEtude, pk=kwargs["pk"])
        contenu = request.POST.get("contenu", "").strip()

        if contenu:
            mots_interdits = set(MotInterdit.objects.values_list("mot", flat=True))
            mots_interdits = {m.lower() for m in mots_interdits}

            mots_du_message = {
                mot.strip(string.punctuation).lower()
                for mot in contenu.split()
            }

            contient_mot_interdit = bool(mots_interdits & mots_du_message)

            statut = Message.Statut.EN_ATTENTE if contient_mot_interdit else Message.Statut.VISIBLE

            Message.objects.create(
                groupe=groupe,
                auteur=request.user,
                contenu=contenu,
                statut=statut,
                traite_par_ia=False,
            )

        return redirect("communaute:detail_groupe", pk=groupe.pk)


class SignalerMessageView(LoginRequiredMixin, View):

    SEUIL_ALERTE = 3

    def post(self, request, *args, **kwargs):
        message = get_object_or_404(Message, pk=kwargs["pk"])
        motif = request.POST.get("motif", "").strip()

        _signalement, cree = Signalement.objects.get_or_create(
            message=message,
            signale_par=request.user,
            defaults={"motif": motif},
        )

        if cree:
            django_messages.success(request, "Votre signalement a bien été enregistré.")

            nombre_signalements = message.signalements.count()
            if nombre_signalements >= self.SEUIL_ALERTE and message.statut == Message.Statut.VISIBLE:
                message.statut = Message.Statut.SIGNALE
                message.save()
        else:
            django_messages.info(request, "Vous avez déjà signalé ce message.")

        return redirect("communaute:detail_groupe", pk=message.groupe.pk)

 
 
def _suivis_de_lutilisateur(user):
    """
    Retourne le queryset des SuiviMentor concernant l'utilisateur connecté,
    qu'il soit élève ou mentor. Centralise cette logique pour ne pas la
    dupliquer dans chaque vue.
    """
    if hasattr(user, "profil_eleve"):
        return SuiviMentor.objects.filter(eleve=user.profil_eleve)
    elif hasattr(user, "profil_mentor"):
        return SuiviMentor.objects.filter(mentor=user.profil_mentor)
    return SuiviMentor.objects.none()
 
 
class ListeConversationsView(LoginRequiredMixin, ListView):
    model = SuiviMentor
    template_name = "communaute/liste_conversations.html"
    context_object_name = "suivis"
 
    def get_queryset(self):
        return _suivis_de_lutilisateur(self.request.user).select_related(
            "eleve", "mentor", "matiere"
        )
 
 
class DetailConversationView(LoginRequiredMixin, DetailView):
    model = SuiviMentor
    template_name = "communaute/detail_conversation.html"
    context_object_name = "suivi"
 
    def get_queryset(self):
        # Sécurité : seul un participant (élève ou mentor du suivi) peut
        # accéder à cette conversation. Toute autre tentative reçoit un 404,
        # exactement le même principe que ResultatExamenDetailView.
        return _suivis_de_lutilisateur(self.request.user)
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages_prives"] = self.object.messages_prives.filter(
            statut=MessagePrive.Statut.VISIBLE
        ).select_related("auteur")
        return context
 
 
class EnvoyerMessagePriveView(LoginRequiredMixin, View):
 
    def post(self, request, *args, **kwargs):
        # Même vérification de sécurité : on ne peut écrire que dans une
        # conversation dont on est réellement participant.
        suivi = get_object_or_404(_suivis_de_lutilisateur(request.user), pk=kwargs["pk"])
 
        contenu = request.POST.get("contenu", "").strip()
 
        if contenu:
            statut = (
                MessagePrive.Statut.EN_ATTENTE
                if contient_mot_interdit(contenu)
                else MessagePrive.Statut.VISIBLE
            )
 
            MessagePrive.objects.create(
                suivi=suivi,
                auteur=request.user,
                contenu=contenu,
                statut=statut,
            )
 
            if statut == MessagePrive.Statut.EN_ATTENTE:
                django_messages.info(
                    request,
                    "Ton message contient des termes à vérifier, il sera visible après révision.",
                )
 
        return redirect("communaute:detail_conversation", pk=suivi.pk)
 