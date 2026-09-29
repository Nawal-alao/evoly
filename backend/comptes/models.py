from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from pedagogie.models import ClasseScolaire, Serie


class Eleve(models.Model):
	utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil_eleve")
	prenom = models.CharField(max_length=100)
	nom = models.CharField(max_length=100)
	age = models.PositiveSmallIntegerField()
	classe_scolaire = models.CharField(max_length=10, choices=ClasseScolaire.choices)
	serie = models.CharField(max_length=10, choices=Serie.choices, default=Serie.AUCUNE)
	date_inscription = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.prenom} {self.nom} ({self.classe_scolaire})"


class Mentor(models.Model):
	utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil_mentor")
	prenom = models.CharField(max_length=100)
	nom = models.CharField(max_length=100)
	bio = models.TextField(blank=True)
	matieres = models.ManyToManyField('pedagogie.Matiere', related_name="mentors")
	disponible = models.BooleanField(default=True)

	def __str__(self):
		return f"Mentor {self.prenom} {self.nom}"

	@property
	def note_moyenne(self):
		suivis = self.suivis.filter(note_evaluation__isnull=False)
		if not suivis.exists():
			return None
		return suivis.aggregate(models.Avg("note_evaluation"))["note_evaluation__avg"]


class SuiviMentor(models.Model):
	eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="suivis_mentors")
	mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="suivis")
	matiere = models.ForeignKey('pedagogie.Matiere', on_delete=models.CASCADE)
	date_debut = models.DateTimeField(auto_now_add=True)
	actif = models.BooleanField(default=True)
	note_evaluation = models.PositiveSmallIntegerField(
		null=True, blank=True,
		validators=[MinValueValidator(1), MaxValueValidator(5)],
		help_text="Note de 1 à 5 donnée par l'élève pour cette matière précise."
	)

	def __str__(self):
		return f"{self.eleve} suit {self.mentor} en {self.matiere}"
