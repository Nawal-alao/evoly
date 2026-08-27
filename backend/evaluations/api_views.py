from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Max
from django.db.models.functions import TruncDate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Examen, Question, ReponseEleve, Resultat, Progression, HistoriqueProgression
from .serializers import (
    ExamenSerializer, ExamenDetailSerializer, QuestionSerializer, QuestionCorrectionSerializer,
    ResultatSerializer, ReponseEleveDetailSerializer, ProgressionSerializer,
    HistoriqueProgressionSerializer,
)


def _examens_accessibles_pour(user):
    # Reuse logic similar to ListeExamensDisponiblesView
    if hasattr(user, 'profil_eleve'):
        eleve = user.profil_eleve
        return Examen.objects.filter(
            cours__classe_scolaire=eleve.classe_scolaire,
            cours__serie=eleve.serie,
            cours__statut_validation='VALIDE',
            statut_validation='VALIDE',
            date_publication__lt=timezone.now(),
        ).select_related('cours', 'cours__matiere').order_by('niveau_difficulte', '-date_publication')
    elif hasattr(user, 'profil_mentor'):
        return Examen.objects.filter(
            statut_validation='VALIDE',
            cours__statut_validation='VALIDE',
            date_publication__lt=timezone.now(),
        ).select_related('cours', 'cours__matiere').order_by('niveau_difficulte', '-date_publication')
    return Examen.objects.none()


class ExamensListAPIView(generics.ListAPIView):
    serializer_class = ExamenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _examens_accessibles_pour(self.request.user)


class PasserExamenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        examen = get_object_or_404(_examens_accessibles_pour(request.user), pk=pk)
        questions_sans_groupe = examen.questions.filter(groupe__isnull=True).order_by('id')
        examen_data = ExamenDetailSerializer(examen).data
        questions_data = QuestionSerializer(questions_sans_groupe, many=True).data
        return Response({'examen': examen_data, 'questions': questions_data})


class SoumettreExamenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        examen = get_object_or_404(_examens_accessibles_pour(request.user), pk=pk)
        eleve = request.user.profil_eleve

        questions = list(examen.questions.all())
        total_questions = len(questions)
        nombre_correct = 0

        # Repassage : supprimer les anciennes réponses
        ReponseEleve.objects.filter(
            eleve=eleve, question__examen=examen,
        ).delete()

        # Expect payload: {'reponses': [{'question_id': id, 'reponse': '...'}, ...]}
        reponses_payload = request.data.get('reponses', [])
        # Create a mapping from question id to provided answer
        reponses_map = {int(r.get('question_id')): r.get('reponse', '') for r in reponses_payload}

        for question in questions:
            reponse_donnee = reponses_map.get(question.id, '')
            correct = (reponse_donnee.strip() == question.bonne_reponse.strip())
            ReponseEleve.objects.create(
                eleve=eleve,
                question=question,
                reponse_donnee=reponse_donnee,
                correct=correct,
            )
            if correct:
                nombre_correct += 1

        # Recalculate progression for this matiere
        progression, _ = Progression.objects.get_or_create(eleve=eleve, matiere=examen.cours.matiere)
        progression.recalculer()

        note = (nombre_correct / total_questions) * 20 if total_questions > 0 else 0

        resultat, _ = Resultat.objects.update_or_create(
            eleve=eleve,
            examen=examen,
            defaults={"note": note},
        )

        # Return the created resultat detail
        serializer = ResultatSerializer(resultat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResultatDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ResultatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Resultat.objects.filter(eleve=self.request.user.profil_eleve)


class MesProgressionsAPIView(generics.ListAPIView):
    serializer_class = ProgressionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Progression.objects.filter(eleve=self.request.user.profil_eleve).select_related('matiere')


class HistoriqueProgressionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        eleve = request.user.profil_eleve
        matiere_id = request.query_params.get('matiere')

        matieres_avec_historique = (
            HistoriqueProgression.objects
            .filter(eleve=eleve)
            .values_list('matiere_id', flat=True)
            .distinct()
        )

        if not matiere_id:
            from pedagogie.models import Matiere
            matieres = Matiere.objects.filter(id__in=matieres_avec_historique).values('id', 'nom')
            return Response({
                'matieres': list(matieres),
                'points': [],
            })

        il_y_a_30_jours = timezone.now() - timezone.timedelta(days=30)

        # Pour chaque jour, récupérer l'id du snapshot le plus tardif
        latest_ids = (
            HistoriqueProgression.objects
            .filter(eleve=eleve, matiere_id=matiere_id, date_snapshot__gte=il_y_a_30_jours)
            .annotate(jour=TruncDate('date_snapshot'))
            .values('jour')
            .annotate(dernier_id=Max('id'))
            .values_list('dernier_id', flat=True)
        )

        points = (
            HistoriqueProgression.objects
            .filter(id__in=latest_ids)
            .order_by('date_snapshot')
            .values('date_snapshot', 'niveau_maitrise')
        )

        return Response({
            'matieres': [],
            'points': list(points),
        })
