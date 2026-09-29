from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from communaute.models import GroupeEtude, Message, MessagePrive, MotInterdit, Signalement
from communaute.services import contient_mot_interdit
from comptes.models import Eleve, Mentor, SuiviMentor
from pedagogie.models import ClasseScolaire, Matiere, Serie


class _FixturesCommunaute(TestCase):
    def setUp(self):
        self.maths = Matiere.objects.create(nom="Mathématiques")
        self.physique = Matiere.objects.create(nom="Physique")

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
        self.mentor.matieres.set([self.maths])

        self.groupe_valide = GroupeEtude.objects.create(
            nom="Groupe maths",
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            matiere=self.maths,
            statut_validation=GroupeEtude.StatutValidation.VALIDE,
        )
        self.groupe_attente = GroupeEtude.objects.create(
            nom="Groupe en attente",
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            matiere=self.maths,
            statut_validation=GroupeEtude.StatutValidation.EN_ATTENTE,
        )
        self.groupe_autre_classe = GroupeEtude.objects.create(
            nom="Groupe 5ème",
            classe_scolaire=ClasseScolaire.CINQUIEME,
            serie=Serie.A,
            matiere=self.maths,
            statut_validation=GroupeEtude.StatutValidation.VALIDE,
        )
        self.groupe_autre_matiere = GroupeEtude.objects.create(
            nom="Groupe physique",
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
            matiere=self.physique,
            statut_validation=GroupeEtude.StatutValidation.VALIDE,
        )


class ListeGroupesViewTests(_FixturesCommunaute):
    def setUp(self):
        super().setUp()
        self.url = reverse("communaute:liste_groupes")

    def test_acces_reserve_aux_utilisateurs_connectes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_eleve_voit_tous_les_groupes_valides_de_sa_classe(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        # Le filtre élève porte sur la classe et la série, pas sur la matière :
        # les groupes validés de 6ème A sont tous visibles, quelle que soit
        # la matière. Trié par matière puis par nom.
        self.assertEqual(
            list(response.context["groupes"]),
            [self.groupe_valide, self.groupe_autre_matiere],
        )

    def test_mentor_voit_les_groupes_de_ses_matieres_toutes_classes(self):
        self.client.force_login(self.user_mentor)

        response = self.client.get(self.url)

        # Le mentor n'est pas filtré par classe : il voit les groupes de
        # matières qu'il enseigne, en attente de validation exclus.
        self.assertEqual(
            list(response.context["groupes"]),
            [self.groupe_autre_classe, self.groupe_valide],
        )


class DetailGroupeViewTests(_FixturesCommunaute):
    def setUp(self):
        super().setUp()
        self.url = reverse("communaute:detail_groupe", args=[self.groupe_valide.pk])
        self.message_visible = Message.objects.create(
            groupe=self.groupe_valide,
            auteur=self.user_eleve,
            contenu="Bonjour",
        )
        self.message_masque = Message.objects.create(
            groupe=self.groupe_valide,
            auteur=self.user_eleve,
            contenu="À masquer",
            statut=Message.Statut.MASQUE,
        )

    def test_seuls_les_messages_visibles_sont_affiches(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["messages_groupe"]), [self.message_visible])

    def test_groupe_dune_autre_classe_renvoie_404(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("communaute:detail_groupe", args=[self.groupe_autre_classe.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_groupe_non_valide_renvoie_404(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("communaute:detail_groupe", args=[self.groupe_attente.pk])
        )

        self.assertEqual(response.status_code, 404)


class SignalerMessageViewTests(_FixturesCommunaute):
    def setUp(self):
        super().setUp()
        self.message = Message.objects.create(
            groupe=self.groupe_valide, auteur=self.user_mentor, contenu="Contenu signalé"
        )
        self.url = reverse("communaute:signaler_message", args=[self.message.pk])

    def _signaler(self, username):
        """Connecte un nouvel élève et lui fait signaler le message."""
        signaleur = User.objects.create_user(username=username, password="azerty123")
        Eleve.objects.create(
            utilisateur=signaleur,
            prenom=username.capitalize(),
            nom="Test",
            age=15,
            classe_scolaire=ClasseScolaire.SIXIEME,
            serie=Serie.A,
        )
        self.client.force_login(signaleur)
        return self.client.post(self.url, {"motif": "Harcèlement"})

    def test_le_message_est_signale_au_dela_du_seuil(self):
        self._signaler("carla")
        self._signaler("dan")

        self.message.refresh_from_db()
        self.assertEqual(self.message.statut, Message.Statut.VISIBLE)
        self.assertEqual(self.message.signalements.count(), 2)

        self._signaler("eva")

        self.message.refresh_from_db()
        self.assertEqual(self.message.statut, Message.Statut.SIGNALE)
        self.assertEqual(self.message.signalements.count(), 3)

    def test_signalement_en_double_ne_cree_pas_de_doublon(self):
        self.client.force_login(self.user_eleve)

        self.client.post(self.url, {"motif": "Harcèlement"})
        response = self.client.post(self.url, {"motif": "Harcèlement"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Signalement.objects.filter(message=self.message).count(), 1)

    def test_un_message_deja_masque_nest_pas_re_statue(self):
        self.message.statut = Message.Statut.MASQUE
        self.message.save()

        for username in ("carla", "dan", "eva"):
            self._signaler(username)

        self.message.refresh_from_db()
        # Le seuil est atteint, mais la vue ne touche que les messages visibles.
        self.assertEqual(self.message.statut, Message.Statut.MASQUE)


class ConversationTests(_FixturesCommunaute):
    def setUp(self):
        super().setUp()
        self.suivi = SuiviMentor.objects.create(
            eleve=self.eleve, mentor=self.mentor, matiere=self.maths
        )
        self.suivi_autre = SuiviMentor.objects.create(
            eleve=Eleve.objects.create(
                utilisateur=User.objects.create_user(username="carla", password="azerty123"),
                prenom="Carla",
                nom="Petit",
                age=15,
                classe_scolaire=ClasseScolaire.SIXIEME,
                serie=Serie.A,
            ),
            mentor=self.mentor,
            matiere=self.maths,
        )

    def test_liste_des_conversations_de_leleve(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(reverse("communaute:liste_conversations"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["suivis"]), [self.suivi])

    def test_liste_des_conversations_du_mentor(self):
        self.client.force_login(self.user_mentor)

        response = self.client.get(reverse("communaute:liste_conversations"))

        self.assertEqual(
            set(response.context["suivis"]),
            {self.suivi, self.suivi_autre},
        )

    def test_conversation_dun_tiers_renvoie_404(self):
        self.client.force_login(self.user_eleve)

        response = self.client.get(
            reverse("communaute:detail_conversation", args=[self.suivi_autre.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_envoi_par_un_participant(self):
        self.client.force_login(self.user_eleve)

        response = self.client.post(
            reverse("communaute:envoyer_message_prive", args=[self.suivi.pk]),
            {"contenu": "Bonjour, une question"},
        )

        self.assertRedirects(
            response, reverse("communaute:detail_conversation", args=[self.suivi.pk])
        )
        message = MessagePrive.objects.get(suivi=self.suivi)
        self.assertEqual(message.auteur, self.user_eleve)
        self.assertEqual(message.statut, MessagePrive.Statut.VISIBLE)

    def test_envoi_par_un_tiers_renvoie_404(self):
        intrus = User.objects.create_user(username="intrus", password="azerty123")
        self.client.force_login(intrus)

        response = self.client.post(
            reverse("communaute:envoyer_message_prive", args=[self.suivi.pk]),
            {"contenu": "Message intruder"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(MessagePrive.objects.exists())


class ContientMotInterditTests(TestCase):
    def test_detecte_un_mot_interdit_ponctue(self):
        MotInterdit.objects.create(mot="idiot")

        self.assertTrue(contient_mot_interdit("Tu es un IDIOT !"))
        self.assertTrue(contient_mot_interdit("idiot,"))
        self.assertFalse(contient_mot_interdit("Tu es maladroit"))
        self.assertFalse(contient_mot_interdit("Les idioties sont utiles"))
