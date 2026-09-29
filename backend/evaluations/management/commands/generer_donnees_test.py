"""
python manage.py generer_donnees_test --eleve eleve@test.com --matiere "Mathématiques"

Crée des examens fictifs + résultats + historique de progression
répartis sur les 10 derniers jours, pour tester le graphique d'évolution.

Utilise --detruire pour supprimer toutes les données de test.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from comptes.models import Eleve
from evaluations.models import (
    Examen,
    ExerciceGroupe,
    HistoriqueProgression,
    Progression,
    Question,
    ReponseEleve,
    Resultat,
)
from pedagogie.models import Cours, Matiere

PREFIXE_TEST = "TEST-GRAPHIQUE"


class Command(BaseCommand):
    help = "Génère ou détruit des données de test pour le graphique d'évolution."

    def add_arguments(self, parser):
        parser.add_argument("--eleve", required=True, help="Email ou username de l'élève")
        parser.add_argument("--matiere", required=True, help="Nom de la matière")
        parser.add_argument("--jours", type=int, default=10, help="Nombre de jours (défaut: 10)")
        parser.add_argument("--par-jour", type=int, default=2, help="Examens par jour (défaut: 2)")
        parser.add_argument("--detruire", action="store_true", help="Supprime les données de test")

    def handle(self, *args, **options):
        if options["detruire"]:
            self._detruire()
            return

        self._creer(options)

    def _creer(self, options):
        identifiant = options["eleve"]
        try:
            eleve = Eleve.objects.select_related("utilisateur").get(
                utilisateur__email__iexact=identifiant
            )
        except Eleve.DoesNotExist:
            try:
                eleve = Eleve.objects.select_related("utilisateur").get(
                    utilisateur__username__iexact=identifiant
                )
            except Eleve.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f"Élève introuvable : « {identifiant} »\n"
                    f"  → Vérifie l'email ou le username dans admin Django (comptes → utilisateurs)"
                ))
                return

        matiere = Matiere.objects.filter(nom__icontains=options["matiere"]).first()
        if not matiere:
            self.stderr.write(self.style.ERROR(
                f"Matière introuvable : {options['matiere']}"
            ))
            return

        cours = Cours.objects.filter(matiere=matiere).first()
        if not cours:
            self.stderr.write(self.style.ERROR(
                f"Aucun cours trouvé pour la matière « {matiere.nom} »"
            ))
            return

        nb_jours = options["jours"]
        par_jour = options["par_jour"]
        now = timezone.now()

        # Niveaux de maîtrise simulés : tendance croissante + bruit
        base_niveaux = [25, 35, 42, 50, 58, 62, 68, 74, 78, 82]
        niveaux = [base_niveaux[min(i, len(base_niveaux) - 1)] for i in range(nb_jours * par_jour)]

        examens_crees = []
        historique_crees = []

        idx = 0
        for jour_offset in range(nb_jours, 0, -1):
            date_jour = now - timedelta(days=jour_offset)
            for rang in range(par_jour):
                # Date décalée de quelques minutes pour chaque examen du même jour
                date_exam = date_jour.replace(hour=8 + rang * 3, minute=30, second=0, microsecond=0)

                # --- Examen ---
                examen = Examen.objects.create(
                    titre=f"{PREFIXE_TEST} Examen J-{jour_offset}/{rang+1}",
                    cours=cours,
                    type_generation=Examen.TypeGeneration.MANUEL,
                    statut_validation=Examen.StatutValidation.VALIDE,
                    niveau_difficulte=Examen.NiveauDifficulte.FACILE,
                    date_publication=date_exam,
                    date_validation=date_exam,
                )

                # --- ExerciceGroupe + Questions ---
                groupe = ExerciceGroupe.objects.create(
                    examen=examen,
                    enonce_principal=f"<p>Exercice de test J-{jour_offset}</p>",
                    ordre=1,
                )
                for qi in range(3):
                    Question.objects.create(
                        examen=examen,
                        groupe=groupe,
                        ordre_dans_groupe=qi + 1,
                        enonce=f"Question {qi+1} de test",
                        type_question=Question.Type.COURTE,
                        notion=f"Notion {qi+1}",
                        bonne_reponse=f"réponse {qi+1}",
                    )

                # --- Résultat ---
                niveau = Decimal(str(random.uniform(
                    max(0, niveaux[idx] - 8),
                    min(100, niveaux[idx] + 8)
                ))).quantize(Decimal("0.01"))
                note = (niveau / 100) * 20

                resultat = Resultat.objects.create(
                    eleve=eleve,
                    examen=examen,
                    note=note,
                )
                # Override date_passage (auto_now_add ne permet pas de définir directement)
                Resultat.objects.filter(pk=resultat.pk).update(date_passage=date_exam)

                # --- HistoriqueProgression ---
                hp = HistoriqueProgression(
                    eleve=eleve,
                    matiere=matiere,
                    niveau_maitrise=niveau,
                )
                hp.save()
                # Override date_snapshot
                HistoriqueProgression.objects.filter(pk=hp.pk).update(date_snapshot=date_exam)
                historique_crees.append(hp)

                examens_crees.append(examen)
                idx += 1

        # --- Progression globale ---
        progression, _ = Progression.objects.get_or_create(eleve=eleve, matiere=matiere)
        progression.recalculer()

        self.stdout.write(self.style.SUCCESS(
            f"Créé : {len(examens_crees)} examens, {len(historique_crees)} snapshots "
            f"sur {nb_jours} jours pour {eleve} / {matiere.nom}"
        ))

    def _detruire(self):
        examens = Examen.objects.filter(titre__startswith=PREFIXE_TEST)
        nb_examens = examens.count()

        # Récupérer les (eleve, matiere) concernés avant suppression
        paires = (
            examens
            .values_list("cours__matiere_id", flat=True)
            .distinct()
        )

        Resultat.objects.filter(examen__in=examens).delete()
        ReponseEleve.objects.filter(question__examen__in=examens).delete()
        examens.delete()

        # Supprimer les snapshots d'historique liés à ces matières
        # pour lesquels il n'existe plus aucun Resultat
        hp_a_supprimer = []
        for hp in HistoriqueProgression.objects.filter(matiere_id__in=paires):
            a_un_resultat = Resultat.objects.filter(
                eleve=hp.eleve,
                examen__cours__matiere=hp.matiere,
            ).exists()
            if not a_un_resultat:
                hp_a_supprimer.append(hp.id)
        HistoriqueProgression.objects.filter(id__in=hp_a_supprimer).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Détruit : {nb_examens} examens de test + {len(hp_a_supprimer)} snapshots"
        ))
