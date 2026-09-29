"""
evaluations/services.py — Génération d'examen par IA (Cohere)
===============================================================================
Logique métier isolée du code d'admin. N'importe quel endroit du projet
(a$dmin, commande, vue future) peut réutiliser cette fonction sans
dupliquer de code.

Structure de réponse attendue de Cohere :
  - "exercices" → ExerciceGroupe + Question(COURTE) en étapes
"""

import json
import re

import cohere
from django.conf import settings
from django.utils import timezone

from .models import Examen, ExerciceGroupe, Question


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
    "required": ["exercices"],
    "properties": {
        "exercices": {
            "type": "array",
            "description": "Exercices décomposés en étapes courtes et vérifiables.",
            "items": {
                "type": "object",
                "required": ["enonce_principal", "etapes"],
                "properties": {
                    "enonce_principal": {
                        "type": "string",
                        "description": "Énoncé complet du problème, affiché une seule fois au-dessus des étapes.",
                    },
                    "etapes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["enonce", "notion", "reponse_courte"],
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
                        },
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Prompt système
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


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def generer_examen_ia(cours, nombre_questions=5, niveau_difficulte="FACILE", utilisateur_createur=None):
    """
    Génère un examen via Cohere : des exercices décomposés en étapes courtes
    et vérifiables automatiquement.
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

    message_utilisateur = (
        f"Génère un examen en français, niveau de difficulté « {niveau_difficulte} ».\n"
        f"Nombre total d'éléments : {nombre_questions}.\n\n"
        f"Chaque exercice doit être décomposé en étapes courtes et vérifiables.\n\n"
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

    examen = Examen.objects.create(
        titre=f"Examen — {cours.titre}",
        cours=cours,
        type_generation=Examen.TypeGeneration.IA,
        statut_validation=Examen.StatutValidation.EN_ATTENTE,
        niveau_difficulte=niveau_difficulte,
        date_publication=timezone.now(),
    )

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

    return examen


# ---------------------------------------------------------------------------
# Correction des réponses mathématiques (LaTeX)
# ---------------------------------------------------------------------------

_LATEX_ESPACES = re.compile(r"\\(?:,|;|:|!| |quad|qquad)")


def _retirer_delimitieurs(expr):
    """Retire les délimiteurs de math ($, $$, \\( \\), \\[ \\]) autour d'une chaîne."""
    for gauche, droite in (("$$", "$$"), ("$", "$"), (r"\(", r"\)"), (r"\[", r"\]")):
        if expr.startswith(gauche) and expr.endswith(droite) and len(expr) > len(gauche) + len(droite):
            return expr[len(gauche):-len(droite)]
    return expr


def _retirer_zero_initiaux(expr):
    """0999 -> 999 (conserve la valeur numérique 999)."""
    return re.sub(r"\b0+(\d)", r"\1", expr)


def _normaliser_latex(expr):
    """
    Normalise une expression LaTeX pour une comparaison tolérante.

    - supprime les espaces sémantiques LaTeX (\\,, \\;, \\ , \\quad...)
    - retire les accolades autour d'un nombre ou d'un unique token
    - compacte tous les espaces
    - retire les zéros initiaux des nombres
    """
    expr = _retirer_delimitieurs((expr or "").strip())
    expr = _LATEX_ESPACES.sub("", expr)
    # zéros initiaux : tant que les nombres sont isolés par leurs accolades
    # (mot-frontière présent), 0999 -> 999 sans changer 230999.
    expr = _retirer_zero_initiaux(expr)
    # accolades autour d'un nombre décimal
    expr = re.sub(r"\{(-?\d+(?:\.\d+)?|-\d+)\}", r"\1", expr)
    # accolades autour d'un unique token (lettre, signe)
    expr = re.sub(r"\{([a-zA-Z])\}", r"\1", expr)
    expr = re.sub(r"\s+", "", expr)
    return expr


def reponses_equivalentes(reponse_donnee, bonne_reponse, tolerant=True):
    """
    Compare une réponse élève à la bonne réponse, en supportant le LaTeX.

    - comparaison stricte après normalisation (espaces, accolades, zéros)
    - si non égal et `tolerant` : retente en ignorant les délimiteurs `{}`
      restants ou les commandes de format mineures.
    """
    if bonne_reponse is None:
        return False
    donnee = _normaliser_latex(reponse_donnee or "")
    attendue = _normaliser_latex(bonne_reponse)
    if donnee and donnee == attendue:
        return True
    if not tolerant:
        return False
    # tentative tolérante : vider les accolades restantes
    donnee_libre = donnee.replace("{", "").replace("}", "")
    attendue_libre = attendue.replace("{", "").replace("}", "")
    return bool(donnee_libre) and donnee_libre == attendue_libre
