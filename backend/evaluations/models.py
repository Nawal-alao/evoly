from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import User



class Examen(models.Model):
    class TypeGeneration(models.TextChoices):
        IA = "IA", "Généré par IA"
        MANUEL = "MANUEL", "Créé par un mentor/professeur"
 
    class StatutValidation(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        VALIDE = "VALIDE", "Validé"
        REJETE = "REJETE", "Rejeté"
 
    # NOUVEAU
    class NiveauDifficulte(models.TextChoices):
        FACILE = "FACILE", "Facile"
        MOYEN = "MOYEN", "Moyen"
        DIFFICILE = "DIFFICILE", "Difficile"
 
    titre = models.CharField(max_length=200)
    cours = models.ForeignKey("pedagogie.Cours", on_delete=models.CASCADE, related_name="examens")
    type_generation = models.CharField(max_length=10, choices=TypeGeneration.choices)
    date_publication = models.DateTimeField()
    statut_validation = models.CharField(
        max_length=10, choices=StatutValidation.choices, default=StatutValidation.EN_ATTENTE
    )
    professeur_validateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="examens_valides"
    )
    date_validation = models.DateTimeField(null=True, blank=True)
 
    # NOUVEAU
    niveau_difficulte = models.CharField(
        max_length=10, choices=NiveauDifficulte.choices, default=NiveauDifficulte.MOYEN
    )
 
    def __str__(self):
        return f"{self.titre} ({self.get_niveau_difficulte_display()})"
 
 
 
class ExerciceGroupe(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="exercices_groupes")
    enonce_principal = CKEditor5Field(config_name='default')
    ordre = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["ordre"]

    def __str__(self):
        return f"Exercice {self.ordre} — {self.examen}"


class Question(models.Model):
    class Type(models.TextChoices):
        CHOIX_MULTIPLE = "QCM", "Choix multiple"
        REPONSE_LIBRE = "LIBRE", "Réponse libre"
        COURTE = "COURTE", "Réponse courte"

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="questions")
    groupe = models.ForeignKey(
        ExerciceGroupe, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="etapes",
    )
    ordre_dans_groupe = models.PositiveSmallIntegerField(null=True, blank=True)
 
    # AVANT : enonce = models.TextField()
    enonce = CKEditor5Field(config_name='default')
 
    type_question = models.CharField(max_length=10, choices=Type.choices, default=Type.CHOIX_MULTIPLE)
    notion = models.CharField(max_length=150)
    choix_reponses = models.JSONField(null=True, blank=True)
    bonne_reponse = models.CharField(max_length=500)
 
    def __str__(self):
        return f"{self.enonce[:50]}..."


class Resultat(models.Model):
	eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="resultats")
	examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="resultats")
	note = models.DecimalField(max_digits=5, decimal_places=2)
	date_passage = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("eleve", "examen")

	def __str__(self):
		return f"{self.eleve} - {self.examen} : {self.note}"


class ReponseEleve(models.Model):
	eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="reponses")
	question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="reponses")
	reponse_donnee = models.CharField(max_length=500)
	correct = models.BooleanField()
	date_reponse = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.eleve} -> {self.question} ({'OK' if self.correct else 'KO'})"


class Progression(models.Model):
	eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="progressions")
	matiere = models.ForeignKey('pedagogie.Matiere', on_delete=models.CASCADE, related_name="progressions")
	niveau_maitrise = models.DecimalField(
		max_digits=5, decimal_places=2, default=0,
		help_text="Score de maîtrise global sur cette matière (0 à 100)."
	)
	notions_faibles = models.JSONField(
		default=list, blank=True,
		help_text="Liste des notions où l'élève est en difficulté (calculé depuis ReponseEleve)."
	)
	derniere_mise_a_jour = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ("eleve", "matiere")

	def recalculer(self):
		reponses = ReponseEleve.objects.filter(
			eleve=self.eleve,
			question__examen__cours__matiere=self.matiere,
		)
		total = reponses.count()
		if total == 0:
			self.niveau_maitrise = 0
			self.notions_faibles = []
		else:
			correctes = reponses.filter(correct=True).count()
			self.niveau_maitrise = (correctes / total) * 100

			notions = reponses.values("question__notion").distinct()
			notions_faibles = []
			for n in notions:
				notion = n["question__notion"]
				reponses_notion = reponses.filter(question__notion=notion)
				taux_reussite = reponses_notion.filter(correct=True).count() / reponses_notion.count()
				if taux_reussite < 0.5:
					notions_faibles.append(notion)
			self.notions_faibles = notions_faibles

		self.save()

	def __str__(self):
		return f"Progression {self.eleve} - {self.matiere} ({self.niveau_maitrise}%)"