from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from abonnements.models import Abonnement
from comptes.models import Eleve, Mentor, SuiviMentor
from evaluations.models import Progression
from pedagogie.models import ClasseScolaire, Cours, Matiere, Serie


class AccueilViewTests(TestCase):
    def test_accueil_est_publique(self):
        response = self.client.get(reverse("dashboard:accueil"))

        self.assertEqual(response.status_code, 200)


class DashboardEleveViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="azerty123")
        self.eleve = Eleve.objects.create(
            utilisateur=self.user,
            prenom="Alice",
            nom="Martin",
            age=15,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self.url = reverse("dashboard:dashboard_eleve")

        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.cours = Cours.objects.create(
            titre="Cours de maths",
            description="",
            matiere=self.maths,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            contenu="Contenu",
            statut_validation=Cours.StatutValidation.VALIDE,
        )
        # « progressions » sur le dashboard désigne la progression par matière
        # (evaluations.Progression), pas la progression de lecture des cours.
        self.progression = Progression.objects.create(
            eleve=self.eleve, matiere=self.maths, niveau_maitrise=75
        )

        self.mentor = Mentor.objects.create(
            utilisateur=User.objects.create_user(username="bob", password="azerty123"),
            prenom="Bob",
            nom="Durand",
        )
        self.suivi_actif = SuiviMentor.objects.create(
            eleve=self.eleve, mentor=self.mentor, matiere=self.maths
        )
        self.suivi_inactif = SuiviMentor.objects.create(
            eleve=self.eleve, mentor=self.mentor, matiere=self.maths, actif=False
        )

    def test_acces_reserve_aux_utilisateurs_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_contexte_du_dashboard_eleve(self):
        Abonnement.objects.create(
            eleve=self.eleve,
            formule=Abonnement.Formule.MENSUEL,
            statut=Abonnement.Statut.ACTIF,
            date_fin=timezone.now() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["eleve"], self.eleve)
        self.assertEqual(list(response.context["progressions"]), [self.progression])
        self.assertIsNotNone(response.context["abonnement"])
        # Seuls les suivis actifs doivent remonter.
        self.assertEqual(list(response.context["suivis_mentors"]), [self.suivi_actif])
        self.assertNotIn(self.suivi_inactif, response.context["suivis_mentors"])


class DashboardMentorViewTests(TestCase):
    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.user_mentor = User.objects.create_user(username="bob", password="azerty123")
        self.mentor = Mentor.objects.create(
            utilisateur=self.user_mentor, prenom="Bob", nom="Durand"
        )
        self.url = reverse("dashboard:dashboard_mentor")

        self.eleve1 = Eleve.objects.create(
            utilisateur=User.objects.create_user(username="alice", password="azerty123"),
            prenom="Alice",
            nom="Martin",
            age=15,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self.eleve2 = Eleve.objects.create(
            utilisateur=User.objects.create_user(username="carla", password="azerty123"),
            prenom="Carla",
            nom="Petit",
            age=16,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self.suivi_actif = SuiviMentor.objects.create(
            eleve=self.eleve1, mentor=self.mentor, matiere=self.maths, note_evaluation=5
        )
        self.suivi_inactif = SuiviMentor.objects.create(
            eleve=self.eleve2, mentor=self.mentor, matiere=self.maths, actif=False
        )

    def test_acces_reserve_aux_utilisateurs_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_contexte_du_dashboard_mentor(self):
        self.client.force_login(self.user_mentor)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mentor"], self.mentor)
        self.assertEqual(
            set(response.context["suivis"]),
            {self.suivi_actif, self.suivi_inactif},
        )
        self.assertEqual(
            set(response.context["eleves"]),
            {self.eleve1, self.eleve2},
        )
        self.assertEqual(list(response.context["suivis_actifs"]), [self.suivi_actif])
        self.assertEqual(response.context["note_moyenne"], 5)
