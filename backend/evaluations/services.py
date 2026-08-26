"""
evaluations/services.py — Génération d'examen par IA (Cohere)
===============================================================================
Logique métier isolée du code d'admin. N'importe quel endroit du projet
(admin, commande, vue future) peut réutiliser cette fonction sans
dupliquer de code.

Structure de réponse attendue de Cohere :
  - "exercices"   → ExerciceGroupe + Question(COURTE) en étapes
  - "questions_qcm" → Question(QCM) classiques (FACILE uniquement)
"""

import json
import re
import cohere
from django.conf import settings
from django.utils import timezone

from .models import Examen, Question, ExerciceGroupe


def _texte_brut(contenu_html):
    """
    Retire les balises HTML d'une séquence (contenu CKEditor) pour
    obtenir un texte simple à envoyer au modèle.
    """
    sans_balises = re.sub(r"<[^>]+>", " ", contenu_html)
    return re.sub(r"\s+", " ", sans_balises).strip()


# ---------------------------------------------------------------------------
# Schéma JSON envoyé à Cohere
# ---------------------------------------------------------------------------

SCHEMA_REPONSE = {
    "type": "object",
    "properties": {
        "exercices": {
            "type": "array",
            "description": "Exercices décomposés en étapes courtes et vérifiables.",
            "items": {
                "type": "object",
                "properties": {
                    "enonce_principal": {
                        "type": "string",
                        "description": "Énoncé complet du problème, affiché une seule fois au-dessus des étapes.",
                    },
                    "etapes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "enonce": {
                                    "type": "string",
                                    "description": "Question courte et précise (un calcul, une valeur, un mot).",
                                },
                                "notion": {
                                    "type": "string",
                                    "description": "Thème précis évalué.",
                                },
                                "reponse_courte": {
                                    "type": "string",
                                    "description": "Réponse exacte en un nombre, une expression courte ou un mot.",
                                },
                            },
                            "required": ["enonce", "notion", "reponse_courte"],
                        },
                    },
                },
                "required": ["enonce_principal", "etapes"],
            },
        },
        "questions_qcm": {
            "type": "array",
            "description": "Questions à choix multiple (UNIQUEMENT pour le niveau FACILE).",
            "items": {
                "type": "object",
                "properties": {
                    "enonce": {"type": "string"},
                    "notion": {
                        "type": "string",
                        "description": "Thème précis évalué.",
                    },
                    "choix": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exactement 4 propositions de réponse.",
                    },
                    "bonne_reponse": {
                        "type": "string",
                        "description": "Doit correspondre exactement à l'une des valeurs de 'choix'.",
                    },
                },
                "required": ["enonce", "notion", "choix", "bonne_reponse"],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Prompt système + instructions par niveau
# ---------------------------------------------------------------------------

PROMPT_SYSTEME = """Tu es un professeur qui conçoit des examens pour des élèves du \
système éducatif béninois. Tu génères du JSON brut, sans texte avant ou après.

RÈGLE ABSOLUE DE DÉCOMPOSITION :
Chaque exercice doit être décomposé en plusieurs PETITES étapes courtes et \
vérifiables automatiquement (un nombre, une expression, un mot-clé). JAMAIS \
une seule question ouverte à réponse longue. L'élève progresse pas à pas : \
chaque étape vérifie une sous-compétence précise.

Règles générales :
- Reste strictement dans le contenu fourni, n'invente aucune notion hors programme.
- Ne pose jamais de question qui se résout en retrouvant une phrase copiée-collée du cours.
- Privilégie des mises en situation, des cas à raisonner, des applications concrètes.
- Chaque étape doit avoir une réponse courte et univoque (nombre, expression, mot).
- Réponds UNIQUEMENT en JSON valide, sans aucun texte autour."""


NIVEAUX_INSTRUCTIONS = {
    "FACILE": (
        "Niveau FACILE — autorise les deux formats :\n"
        "1) Exercices décomposés en étapes courtes et vérifiables (champs \"exercices\").\n"
        "2) Questions à choix multiple simples, application directe d'une seule notion "
        "(champs \"questions_qcm\").\n"
        "Tu peux mélanger les deux formats. Application directe, pas de piège, "
        "pour un élève qui découvre le sujet."
    ),
    "MOYEN": (
        "Niveau MOYEN — format EXCLUSIF :\n"
        "Tu dois générer UNIQUEMENT des exercices décomposés en étapes courtes "
        "(champs \"exercices\"). JAMAIS de QCM.\n"
        "Chaque problème est décomposé en plusieurs étapes vérifiables automatiquement. "
        "L'élève combine deux notions ou applique la notion à un cas légèrement "
        "différent de l'exemple du cours.\n"
        "Le champ \"questions_qcm\" ne doit PAS être présent dans ta réponse."
    ),
    "DIFFICILE": (
        "Niveau DIFFICILE — format EXCLUSIF :\n"
        "Tu dois générer UNIQUEMENT des exercices décomposés en étapes courtes "
        "(champs \"exercices\"). JAMAIS de QCM.\n"
        "Chaque problème exige un raisonnement en plusieurs étapes, une mise en "
        "situation complexe, ou la combinaison de plusieurs notions du cours. "
        "Chaque étape reste courte et vérifiable (nombre, expression, mot). "
        "L'élève décompose le raisonnement pas à pas.\n"
        "Le champ \"questions_qcm\" ne doit PAS être présent dans ta réponse."
    ),
}


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def generer_examen_ia(cours, nombre_questions=5, niveau_difficulte="MOYEN", utilisateur_createur=None):
    """
    Génère un examen via Cohere en fonction du niveau de difficulté.

    - FACILE : QCM + exercices en cascade (les deux formats mélangés)
    - MOYEN / DIFFICILE : uniquement des ExerciceGroupe avec étapes COURTE
    """
    sequences = cours.sequences.all()
    contenu_complet = "\n\n".join(
        f"Séquence {s.ordre} — {s.titre} :\n{_texte_brut(s.contenu)}"
        for s in sequences
    )

    if not contenu_complet.strip():
        raise ValueError(
            f"Le cours « {cours.titre} » n'a aucune séquence avec du contenu, "
            "impossible de générer un examen dessus."
        )

    client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)

    instruction_niveau = NIVEAUX_INSTRUCTIONS.get(niveau_difficulte, NIVEAUX_INSTRUCTIONS["MOYEN"])

    message_utilisateur = (
        f"Génère un examen en français, niveau de difficulté « {niveau_difficulte} ».\n"
        f"Nombre total d'éléments : {nombre_questions}.\n\n"
        f"Instructions pour ce niveau :\n{instruction_niveau}\n\n"
        f"Portant sur ce cours de {cours.matiere.nom} "
        f"({cours.get_classe_scolaire_display()}) :\n\n{contenu_complet}"
    )

    reponse = client.chat(
        model="command-r-plus-08-2024",
        messages=[
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": message_utilisateur},
        ],
        response_format={"type": "json_object", "json_schema": SCHEMA_REPONSE},
    )

    donnees = json.loads(reponse.message.content[0].text)

    noms_niveaux = {"FACILE": "Facile", "MOYEN": "Moyen", "DIFFICILE": "Difficile"}
    examen = Examen.objects.create(
        titre=f"Examen {noms_niveaux.get(niveau_difficulte, '')} — {cours.titre}",
        cours=cours,
        type_generation=Examen.TypeGeneration.IA,
        statut_validation=Examen.StatutValidation.EN_ATTENTE,
        niveau_difficulte=niveau_difficulte,
        date_publication=timezone.now(),
    )

    # --- Exercices en cascade (tous les niveaux) ---
    for idx_ex, exercice in enumerate(donnees.get("exercices", []), start=1):
        groupe = ExerciceGroupe.objects.create(
            examen=examen,
            enonce_principal=exercice["enonce_principal"],
            ordre=idx_ex,
        )
        for idx_etape, etape in enumerate(exercice.get("etapes", []), start=1):
            Question.objects.create(
                examen=examen,
                groupe=groupe,
                ordre_dans_groupe=idx_etape,
                enonce=etape["enonce"],
                type_question=Question.Type.COURTE,
                notion=etape["notion"],
                bonne_reponse=etape["reponse_courte"],
            )

    # --- Questions QCM (FACILE uniquement) ---
    for q in donnees.get("questions_qcm", []):
        Question.objects.create(
            examen=examen,
            enonce=q["enonce"],
            type_question=Question.Type.CHOIX_MULTIPLE,
            notion=q["notion"],
            choix_reponses=q["choix"],
            bonne_reponse=q["bonne_reponse"],
        )

    return examen
