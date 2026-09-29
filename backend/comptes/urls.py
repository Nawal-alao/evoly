from django.urls import path

from .views import (
    ConnexionView,
    DeconnexionView,
    InscriptionEleveView,
    InscriptionMentorView,
    ListeMentorsView,
    NoterMentorView,
    ProfilEleveView,
    ProfilMentorView,
    SuivreMentorView,
)

app_name = "comptes"

urlpatterns = [
    path("inscription/eleve/", InscriptionEleveView.as_view(), name="inscription_eleve"),
    path("inscription/mentor/", InscriptionMentorView.as_view(), name="inscription_mentor"),
    path("connexion/", ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", DeconnexionView.as_view(), name="deconnexion"),
    path("mentors/", ListeMentorsView.as_view(), name="liste_mentors"),
    path("mentors/<int:pk>/suivre/", SuivreMentorView.as_view(), name="suivre_mentor"),
    path("profil/eleve/", ProfilEleveView.as_view(), name="profil_eleve"),
    path("profil/mentor/", ProfilMentorView.as_view(), name="profil_mentor"),
    path("mentors/suivi/<int:pk>/noter/", NoterMentorView.as_view(), name="noter_mentor"),

]