from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from comptes.models import Eleve, Mentor
from pedagogie.models import ClasseScolaire, Cours, Matiere, Sequence, Serie


class _FixturesCours(TestCase):
    """Cours de référence : un cours validé de 6ème A, le reste sert de contre-exemple."""

    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")

        self.cours_valide = Cours.objects.create(
            titre="Cours de maths",
            description="",
            matiere=self.maths,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            contenu="Contenu du cours",
            statut_validation=Cours.StatutValidation.VALIDE,
        )
        self.cours_attente = Cours.objects.create(
            titre="Cours en attente",
            description="",
            matiere=self.maths,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            contenu="Contenu",
            statut_validation=Cours.StatutValidation.EN_ATTENTE,
        )
        self.cours_autre_classe = Cours.objects.create(
            titre="Cours de 5ème",
            description="",
            matiere=self.maths,
            classe_scolaire=ClasseScolaire.CINQUIEME,
            serie=Serie.A,
            contenu="Contenu",
            statut_validation=Cours.StatutValidation.VALIDE,
        )

        self.user_eleve = User.objects.create_user(username="alice", password="azerty123")
        self.eleve = Eleve.objects.create(
            utilisateur=self.user_eleve,
            prenom="Alice",
            nom="Martin",
            age=15,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self.user_mentor = User.objects.create_user(username="bob", password="azerty123")
        self.mentor = Mentor.objects.create(
            utilisateur=self.user_mentor, prenom="Bob", nom="Durand"
        )


class ListeCoursViewTests(_FixturesCours):
    def setUp(self):
        super().setUp()
        self.url = reverse("pedagogie:liste_cours")

    def test_acces_reserve_aux_utilisateurs_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_eleve_voit_ses_cours_valides(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        cours = list(response.context["cours_liste"])
        self.assertEqual(cours, [self.cours_valide])

    def test_mentor_voit_tous_les_cours_valides(self):
        self.client.force_login(self.user_mentor)

        response = self.client.get(self.url)

        cours = set(response.context["cours_liste"])
        self.assertEqual(cours, {self.cours_valide, self.cours_autre_classe})


class DetailCoursViewTests(_FixturesCours):
    def setUp(self):
        super().setUp()
        Sequence.objects.create(
            cours=self.cours_valide, titre="Introduction", ordre=1, contenu="<p>Hello</p>"
        )
        Sequence.objects.create(
            cours=self.cours_valide, titre="Exercices", ordre=2, contenu="<p> exos</p>"
        )

    def test_detail_expose_les_sequences_dans_lordre(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("pedagogie:detail_cours", args=[self.cours_valide.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [sequence.ordre for sequence in response.context["sequences"]],
            [1, 2],
        )

    def test_cours_dune_autre_classe_renvoie_404(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("pedagogie:detail_cours", args=[self.cours_autre_classe.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_cours_non_valide_renvoie_404(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("pedagogie:detail_cours", args=[self.cours_attente.pk])
        )

        self.assertEqual(response.status_code, 404)
