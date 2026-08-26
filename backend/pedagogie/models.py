from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


# CHOIX PARTAGÉS (classe scolaire, série)
class ClasseScolaire(models.TextChoices):
	SIXIEME = "6EME", "Sixième"
	CINQUIEME = "5EME", "Cinquième"
	QUATRIEME = "4EME", "Quatrième"
	TROISIEME = "3EME", "Troisième"
	SECONDE = "2ND", "Seconde"
	PREMIERE = "1ERE", "Première"
	TERMINALE = "TLE", "Terminale"


class Serie(models.TextChoices):
	AUCUNE = "AUCUNE", "Aucune (collège)"
	A = "A", "Série A"
	B = "B", "Série B"
	C = "C", "Série C"
	D = "D", "Série D"


class Matiere(models.Model):
	nom = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.nom


class CoefficientMatiere(models.Model):
	matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name="coefficients")
	serie = models.CharField(max_length=10, choices=Serie.choices)
	coefficient = models.PositiveSmallIntegerField(default=1)

	class Meta:
		unique_together = ("matiere", "serie")

	def __str__(self):
		return f"{self.matiere} - {self.serie} (coef {self.coefficient})"


class Cours(models.Model):
	class StatutValidation(models.TextChoices):
		EN_ATTENTE = "EN_ATTENTE", "En attente"
		VALIDE = "VALIDE", "Validé"
		REJETE = "REJETE", "Rejeté"

	titre = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name="cours")
	classe_scolaire = models.CharField(max_length=10, choices=ClasseScolaire.choices)
	serie = models.CharField(max_length=10, choices=Serie.choices, default=Serie.AUCUNE)
	contenu = models.TextField(help_text="Contenu du cours généré par l'IA.")
	source_manuel = models.CharField(max_length=255, blank=True, help_text="Référence du manuel officiel source.")
	statut_validation = models.CharField(
		max_length=10, choices=StatutValidation.choices, default=StatutValidation.EN_ATTENTE
	)
	professeur_validateur = models.ForeignKey(
		'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="cours_valides"
	)
	date_creation = models.DateTimeField(auto_now_add=True)
	date_validation = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"{self.titre} ({self.classe_scolaire}/{self.serie})"


class Sequence(models.Model):
    """
    Une sous-partie d'un Cours. Contenu riche via CKEditor.
    """
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="sequences")
    titre = models.CharField(max_length=200)
    ordre = models.PositiveSmallIntegerField(help_text="Position de la séquence dans le cours (1, 2, 3...).")
    contenu = CKEditor5Field(config_name='contenu_interactif')

    class Meta:
        ordering = ["ordre"]

    def __str__(self):
        return f"{self.cours.titre} — Séquence {self.ordre}: {self.titre}"


class CoursTermine(models.Model):
    eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="cours_termines")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="termine_par")
    date_completion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("eleve", "cours")

    def __str__(self):
        return f"{self.eleve} a terminé {self.cours}"


class CoursFavori(models.Model):
    eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="cours_favoris")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="favori_par")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("eleve", "cours")

    def __str__(self):
        return f"{self.eleve} a en favori {self.cours}"


class CoursProgression(models.Model):
    eleve = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name="progressions_cours")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="progressions")
    derniere_sequence = models.ForeignKey(Sequence, on_delete=models.SET_NULL, null=True, blank=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("eleve", "cours")

    def __str__(self):
        return f"{self.eleve} — {self.cours} — séquence {self.derniere_sequence}"
