from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from abonnements.models import Abonnement
from comptes.models import Eleve
from pedagogie.models import ClasseScolaire, Serie


class _FixturesAbonnement(TestCase):
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

    def _abonner(self, **kwargs):
        defauts = {
            "eleve": self.eleve,
            "formule": Abonnement.Formule.MENSUEL,
            "statut": Abonnement.Statut.ACTIF,
            "date_fin": timezone.now() + timedelta(days=30),
        }
        defauts.update(kwargs)
        return Abonnement.objects.create(**defauts)


class MonAbonnementViewTests(_FixturesAbonnement):
    def setUp(self):
        super().setUp()
        self.url = reverse("abonnements:mon_abonnement")

    def test_acces_reserve_aux_utilisateurs_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_separe_abonnement_actif_et_historique(self):
        actif = self._abonner()
        ancien = self._abonner(statut=Abonnement.Statut.ANNULE)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["abonnement_actif"], actif)
        self.assertEqual(list(response.context["historique"]), [ancien])

    def test_sans_abonnement_le_contexte_reste_vide(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertIsNone(response.context["abonnement_actif"])
        self.assertEqual(list(response.context["historique"]), [])


class SouscrireAbonnementViewTests(_FixturesAbonnement):
    def setUp(self):
        super().setUp()
        self.url = reverse("abonnements:souscrire")
        self.date_fin = (timezone.now() + timedelta(days=365)).isoformat()

    def test_souscription_rattache_labonnement_a_leleve_connecte(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"formule": Abonnement.Formule.ANNUEL, "date_fin": self.date_fin},
        )

        self.assertRedirects(response, reverse("abonnements:mon_abonnement"))
        abonnement = Abonnement.objects.get()
        self.assertEqual(abonnement.eleve, self.eleve)
        self.assertEqual(abonnement.formule, Abonnement.Formule.ANNUEL)
        self.assertEqual(abonnement.statut, Abonnement.Statut.ACTIF)

    def test_date_fin_invalide_est_refusee(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"formule": Abonnement.Formule.MENSUEL, "date_fin": "pas-une-date"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Abonnement.objects.exists())


class AnnulerAbonnementViewTests(_FixturesAbonnement):
    def setUp(self):
        super().setUp()
        self.url = reverse("abonnements:annuler")

    def test_annulation_passe_le_statut_a_annule(self):
        abonnement = self._abonner()
        self.client.force_login(self.user)

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("abonnements:mon_abonnement"))
        abonnement.refresh_from_db()
        self.assertEqual(abonnement.statut, Abonnement.Statut.ANNULE)

    def test_annulation_sans_abonnement_actif_renvoie_404(self):
        self._abonner(statut=Abonnement.Statut.EXPIRE)
        self.client.force_login(self.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)

    def test_un_eleve_ne_peut_pas_annuler_labonnement_dautrui(self):
        abonnement = self._abonner()
        autre = User.objects.create_user(username="carla", password="azerty123")
        autre_eleve = Eleve.objects.create(
            utilisateur=autre,
            prenom="Carla",
            nom="Petit",
            age=16,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self._abonner(eleve=autre_eleve)
        self.client.force_login(autre)

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("abonnements:mon_abonnement"))
        abonnement.refresh_from_db()
        # Seule l'annulation du profil connecté est prise en compte, pas celle d'autrui.
        self.assertEqual(abonnement.statut, Abonnement.Statut.ACTIF)
        self.assertEqual(autre_eleve.abonnements.get().statut, Abonnement.Statut.ANNULE)
