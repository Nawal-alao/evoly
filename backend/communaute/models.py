from django.contrib.auth.models import User
from django.db import models

from pedagogie.models import ClasseScolaire, Serie


class GroupeEtude(models.Model):
	class StatutValidation(models.TextChoices):
		EN_ATTENTE = "EN_ATTENTE", "En attente de validation"
		VALIDE = "VALIDE", "Validé"
		REJETE = "REJETE", "Rejeté"

	nom = models.CharField(max_length=150)
	classe_scolaire = models.CharField(max_length=10, choices=ClasseScolaire.choices)
	serie = models.CharField(max_length=10, choices=Serie.choices, default=Serie.AUCUNE)
	matiere = models.ForeignKey('pedagogie.Matiere', on_delete=models.CASCADE, related_name="groupes_etude")
	statut_validation = models.CharField(
		max_length=12, choices=StatutValidation.choices, default=StatutValidation.EN_ATTENTE
	)
	cree_par = models.ForeignKey(
		User, on_delete=models.SET_NULL, null=True, blank=True, related_name="groupes_crees"
	)

	def __str__(self):
		return self.nom


class MotInterdit(models.Model):
	mot = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.mot


class Message(models.Model):
	class Statut(models.TextChoices):
		VISIBLE = "VISIBLE", "Visible"
		MASQUE = "MASQUE", "Masqué"
		SIGNALE = "SIGNALE", "Signalé"
		EN_ATTENTE = "EN_ATTENTE", "En attente de révision"

	groupe = models.ForeignKey(GroupeEtude, on_delete=models.CASCADE, related_name="messages")
	auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_envoyes")
	contenu = models.TextField()
	date_envoi = models.DateTimeField(auto_now_add=True)
	statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.VISIBLE)
	traite_par_ia = models.BooleanField(default=False)
	score_risque = models.DecimalField(
		max_digits=3, decimal_places=2, null=True, blank=True,
		help_text="Score de risque (0 à 1) donné par l'IA de modération."
	)

	def __str__(self):
		return f"{self.auteur} dans {self.groupe} : {self.contenu[:40]}..."


class Signalement(models.Model):
	message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="signalements")
	signale_par = models.ForeignKey(User, on_delete=models.CASCADE, related_name="signalements_effectues")
	motif = models.CharField(max_length=255)
	date_signalement = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("message", "signale_par")

	def __str__(self):
		return f"Signalement sur {self.message} par {self.signale_par}"
 
 
class MessagePrive(models.Model):
    class Statut(models.TextChoices):
        VISIBLE = "VISIBLE", "Visible"
        MASQUE = "MASQUE", "Masqué"
        EN_ATTENTE = "EN_ATTENTE", "En attente de révision"
 
    suivi = models.ForeignKey(
        "comptes.SuiviMentor", on_delete=models.CASCADE, related_name="messages_prives"
    )
    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_prives_envoyes")
    contenu = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='devoirs/', null=True, blank=True)
    date_envoi = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.VISIBLE)
    lu = models.BooleanField(default=False, help_text="Lu par le destinataire.")
 
    class Meta:
        ordering = ["date_envoi"]
 
    def __str__(self):
        text = self.contenu[:40] if self.contenu else '📷 Image'
        return f"{self.auteur} — {self.suivi} : {text}..."
 