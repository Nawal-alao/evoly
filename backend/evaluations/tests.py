from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes.models import Eleve
from evaluations.models import Examen
from pedagogie.models import ClasseScolaire, Cours, Matiere, Serie


class ListeExamensDisponiblesViewTests(TestCase):
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
        self.matiere = Matiere.objects.create(nom="Mathématiques")

        self.cours_valide = Cours.objects.create(
            titre="Cours de maths",
            description="",
            matiere=self.matiere,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            statut_validation=Cours.StatutValidation.VALIDE,
        )

        self.examen_disponible = Examen.objects.create(
            titre="Examen maths 1",
            cours=self.cours_valide,
            type_generation=Examen.TypeGeneration.MANUEL,
            date_publication=timezone.now() - timedelta(days=1),
            statut_validation=Examen.StatutValidation.VALIDE,
        )

        self.examen_futur = Examen.objects.create(
            titre="Examen maths 2",
            cours=self.cours_valide,
            type_generation=Examen.TypeGeneration.IA,
            date_publication=timezone.now() + timedelta(days=1),
        )

        self.cours_mauvaise_classe = Cours.objects.create(
            titre="Autre classe",
            description="",
            matiere=self.matiere,
            classe_scolaire=ClasseScolaire.CINQUIEME,
            serie=Serie.A,
            statut_validation=Cours.StatutValidation.VALIDE,
        )
        self.examen_mauvaise_classe = Examen.objects.create(
            titre="Examen mauvaise classe",
            cours=self.cours_mauvaise_classe,
            type_generation=Examen.TypeGeneration.MANUEL,
            date_publication=timezone.now() - timedelta(days=2),
        )

    def test_liste_examens_disponibles_pour_eleve(self):
        self.client.login(username="alice", password="azerty123")
        response = self.client.get(reverse("evaluations:liste_examens"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.examen_disponible, response.context["examens_disponibles"])
        self.assertNotIn(self.examen_futur, response.context["examens_disponibles"])
        self.assertNotIn(self.examen_mauvaise_classe, response.context["examens_disponibles"])
