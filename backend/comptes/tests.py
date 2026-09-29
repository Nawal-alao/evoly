from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from abonnements.models import Abonnement
from pedagogie.models import ClasseScolaire, Matiere, Serie

from .models import Eleve, Mentor, SuiviMentor


def _creer_eleve(username="alice", **kwargs):
    user = User.objects.create_user(username=username, password="azerty123")
    defauts = {
        "prenom": "Alice",
        "nom": "Martin",
        "age": 15,
        "classe_scolaire": ClasseScolaire.SIXIEME,
        "serie": Serie.A,
    }
    defauts.update(kwargs)
    return user, Eleve.objects.create(utilisateur=user, **defauts)


def _creer_mentor(username="bob", matieres=(), disponible=True, **kwargs):
    user = User.objects.create_user(username=username, password="azerty123")
    defauts = {"prenom": "Bob", "nom": "Durand", "bio": "", "disponible": disponible}
    defauts.update(kwargs)
    mentor = Mentor.objects.create(utilisateur=user, **defauts)
    mentor.matieres.set(matieres)
    return user, mentor


class InscriptionEleveViewTests(TestCase):
    def setUp(self):
        self.url = reverse("comptes:inscription_eleve")
        self.donnees = {
            "username": "nouvel_eleve",
            "password": "motdepasse123",
            "prenom": "Nina",
            "nom": "Durand",
            "age": 14,
            "classe_scolaire": ClasseScolaire.CINQUIEME,
            "serie": Serie.B,
        }

    def test_inscription_cree_utilisateur_et_profil(self):
        response = self.client.post(self.url, self.donnees)

        self.assertRedirects(response, reverse("comptes:connexion"))
        eleve = Eleve.objects.get(utilisateur__username="nouvel_eleve")
        self.assertEqual(eleve.prenom, "Nina")
        self.assertEqual(eleve.classe_scolaire, ClasseScolaire.CINQUIEME)
        # Le mot de passe doit être haché par Django, jamais stocké en clair.
        self.assertNotEqual(eleve.utilisateur.password, "motdepasse123")
        self.assertTrue(eleve.utilisateur.check_password("motdepasse123"))

    def test_inscription_refusee_si_username_deja_pris(self):
        User.objects.create_user(username="nouvel_eleve", password="existant123")

        response = self.client.post(self.url, self.donnees)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="nouvel_eleve").count(), 1)
        self.assertFalse(Eleve.objects.filter(utilisateur__username="nouvel_eleve").exists())
        self.assertContains(response, "Ce nom d&#x27;utilisateur est déjà pris")


class ConnexionViewTests(TestCase):
    def setUp(self):
        self.url = reverse("comptes:connexion")

    def test_eleve_est_redirige_vers_son_dashboard(self):
        _creer_eleve(username="alice")

        response = self.client.post(self.url, {"username": "alice", "password": "azerty123"})

        self.assertRedirects(response, reverse("dashboard:dashboard_eleve"))

    def test_mentor_est_redirige_vers_son_dashboard(self):
        _creer_mentor(username="bob")

        response = self.client.post(self.url, {"username": "bob", "password": "azerty123"})

        self.assertRedirects(response, reverse("dashboard:dashboard_mentor"))

    def test_utilisateur_sans_profil_retombe_sur_laccueil(self):
        User.objects.create_user(username="sans_profil", password="azerty123")

        response = self.client.post(self.url, {"username": "sans_profil", "password": "azerty123"})

        self.assertRedirects(response, reverse("dashboard:accueil"))


class ListeMentorsViewTests(TestCase):
    def setUp(self):
        self.url = reverse("comptes:liste_mentors")
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.physique = Matiere.objects.create(nom="Physique")
        self.user, self.eleve = _creer_eleve()
        _, self.mentor_maths = _creer_mentor(
            username="bob", matieres=[self.maths], prenom="Bob"
        )
        _, self.mentor_physique = _creer_mentor(
            username="carla", matieres=[self.physique], prenom="Carla"
        )
        _, self.mentor_indisponible = _creer_mentor(
            username="dan", matieres=[self.maths], prenom="Dan", disponible=False
        )

    def test_liste_reservee_aux_eleves_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_seuls_les_mentors_disponibles_sont_listes(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mentor_maths, response.context["mentors"])
        self.assertIn(self.mentor_physique, response.context["mentors"])
        self.assertNotIn(self.mentor_indisponible, response.context["mentors"])
        self.assertEqual(response.context["matiere_selectionnee"], "")

    def test_filtre_par_matiere(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, {"matiere": self.maths.id})

        mentors = list(response.context["mentors"])
        self.assertEqual(mentors, [self.mentor_maths])
        self.assertEqual(response.context["matiere_selectionnee"], str(self.maths.id))


class SuivreMentorViewTests(TestCase):
    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.user, self.eleve = _creer_eleve()
        _, self.mentor = _creer_mentor(username="bob", matieres=[self.maths])
        self.url = reverse("comptes:suivre_mentor", args=[self.mentor.pk])

    def test_suivi_refuse_sans_abonnement_actif(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"matiere": self.maths.id})

        self.assertRedirects(response, reverse("abonnements:souscrire"))
        self.assertFalse(SuiviMentor.objects.exists())

    def test_suivi_cree_avec_un_abonnement_actif(self):
        Abonnement.objects.create(
            eleve=self.eleve,
            formule=Abonnement.Formule.MENSUEL,
            statut=Abonnement.Statut.ACTIF,
            date_fin=timezone.now() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"matiere": self.maths.id})

        self.assertRedirects(response, reverse("comptes:liste_mentors"))
        self.assertTrue(
            SuiviMentor.objects.filter(
                eleve=self.eleve, mentor=self.mentor, matiere=self.maths
            ).exists()
        )

    def test_suivi_est_idempotent(self):
        Abonnement.objects.create(
            eleve=self.eleve,
            formule=Abonnement.Formule.MENSUEL,
            statut=Abonnement.Statut.ACTIF,
            date_fin=timezone.now() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        self.client.post(self.url, {"matiere": self.maths.id})
        self.client.post(self.url, {"matiere": self.maths.id})

        self.assertEqual(SuiviMentor.objects.count(), 1)


class NoterMentorViewTests(TestCase):
    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.user, self.eleve = _creer_eleve()
        _, self.mentor = _creer_mentor(username="bob", matieres=[self.maths])
        self.suivi = SuiviMentor.objects.create(
            eleve=self.eleve, mentor=self.mentor, matiere=self.maths
        )
        self.url = reverse("comptes:noter_mentor", args=[self.suivi.pk])

    def test_note_valide_est_enregistree(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"note": "4"})

        self.assertRedirects(response, reverse("dashboard:dashboard_eleve"))
        self.suivi.refresh_from_db()
        self.assertEqual(self.suivi.note_evaluation, 4)

    def test_note_hors_bornes_est_refusee(self):
        for note in ["0", "6", "abc"]:
            with self.subTest(note=note):
                self.client.force_login(self.user)

                response = self.client.post(self.url, {"note": note})

                self.assertEqual(response.status_code, 302)
                self.suivi.refresh_from_db()
                self.assertIsNone(self.suivi.note_evaluation)

    def test_un_eleve_ne_peut_pas_noter_le_suivi_dautrui(self):
        autre_user, _ = _creer_eleve(username="carla")
        self.client.force_login(autre_user)

        response = self.client.post(self.url, {"note": "1"})

        self.assertEqual(response.status_code, 404)
        self.suivi.refresh_from_db()
        self.assertIsNone(self.suivi.note_evaluation)


class ProfilEleveViewTests(TestCase):
    def setUp(self):
        self.user, self.eleve = _creer_eleve()
        self.url = reverse("comptes:profil_eleve")

    def test_mise_a_jour_du_profil_connecte(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {
            "prenom": "Alicia",
            "nom": "Martin",
            "age": 16,
            "classe_scolaire": ClasseScolaire.SIXIEME,
            "serie": Serie.A,
        })

        self.assertRedirects(response, self.url)
        self.eleve.refresh_from_db()
        self.assertEqual(self.eleve.prenom, "Alicia")
        self.assertEqual(self.eleve.age, 16)


class MentorNoteMoyenneTests(TestCase):
    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.mentor = _creer_mentor(username="bob", matieres=[self.maths])[1]

    def test_note_moyenne_sans_evaluation(self):
        eleve = Eleve.objects.get(utilisateur=_creer_eleve(username="alice")[0])
        SuiviMentor.objects.create(eleve=eleve, mentor=self.mentor, matiere=self.maths)

        self.assertIsNone(self.mentor.note_moyenne)

    def test_note_moyenne_calculee(self):
        eleve1 = Eleve.objects.get(utilisateur=_creer_eleve(username="alice")[0])
        eleve2 = Eleve.objects.get(utilisateur=_creer_eleve(username="carla")[0])
        SuiviMentor.objects.create(
            eleve=eleve1, mentor=self.mentor, matiere=self.maths, note_evaluation=4
        )
        SuiviMentor.objects.create(
            eleve=eleve2, mentor=self.mentor, matiere=self.maths, note_evaluation=2
        )
        # Un suivi sans note ne doit pas fausser la moyenne.
        SuiviMentor.objects.create(
            eleve=eleve2, mentor=self.mentor, matiere=Matiere.objects.create(nom="Physique")
        )

        self.assertEqual(self.mentor.note_moyenne, 3)
