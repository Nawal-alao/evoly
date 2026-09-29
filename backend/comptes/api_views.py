from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Mentor, SuiviMentor
from .serializers import (
    EleveSerializer,
    InscriptionEleveSerializer,
    InscriptionMentorSerializer,
    MentorSerializer,
    SuiviMentorSerializer,
)


class InscriptionEleveAPIView(generics.CreateAPIView):
    serializer_class = InscriptionEleveSerializer
    permission_classes = [AllowAny]


class InscriptionMentorAPIView(generics.CreateAPIView):
    serializer_class = InscriptionMentorSerializer
    permission_classes = [AllowAny]


class MonProfilAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if hasattr(user, 'profil_eleve'):
            serializer = EleveSerializer(user.profil_eleve)
            return Response(serializer.data)
        if hasattr(user, 'profil_mentor'):
            serializer = MentorSerializer(user.profil_mentor)
            return Response(serializer.data)
        return Response({'detail': 'Aucun profil trouvé pour cet utilisateur.'}, status=404)

    def patch(self, request):
        user = request.user
        if hasattr(user, 'profil_eleve'):
            instance = user.profil_eleve
            serializer = EleveSerializer(instance, data=request.data, partial=True)
        elif hasattr(user, 'profil_mentor'):
            instance = user.profil_mentor
            serializer = MentorSerializer(instance, data=request.data, partial=True)
        else:
            return Response({'detail': 'Aucun profil trouvé pour cet utilisateur.'}, status=404)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ListeMentorsAPIView(generics.ListAPIView):
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Mentor.objects.filter(disponible=True).prefetch_related('matieres')
        matiere_id = self.request.query_params.get('matiere')
        if matiere_id:
            queryset = queryset.filter(matieres__id=matiere_id)
        return queryset.distinct()


class SuivreMentorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not hasattr(user, 'profil_eleve'):
            return Response({'detail': "Seuls les élèves peuvent suivre un mentor."}, status=403)
        eleve = user.profil_eleve
        mentor = get_object_or_404(Mentor, pk=pk)
        matiere_id = request.data.get('matiere')
        if not matiere_id:
            return Response({'detail': 'Paramètre "matiere" requis.'}, status=400)
        from pedagogie.models import Matiere
        matiere = get_object_or_404(Matiere, pk=matiere_id)

        abonnement_actif = eleve.abonnements.filter(statut="ACTIF").exists()
        if not abonnement_actif:
            return Response({'detail': 'Un abonnement actif est nécessaire pour suivre un mentor.'}, status=403)

        suivi, created = SuiviMentor.objects.get_or_create(eleve=eleve, mentor=mentor, matiere=matiere)
        serializer = SuiviMentorSerializer(suivi)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


class MesSuivisAPIView(generics.ListAPIView):
    serializer_class = SuiviMentorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profil_eleve'):
            return SuiviMentor.objects.filter(
                eleve=user.profil_eleve, actif=True
            ).select_related('mentor', 'matiere')
        return SuiviMentor.objects.none()


class SuivisMentorAPIView(generics.ListAPIView):
    serializer_class = SuiviMentorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SuiviMentor.objects.filter(
            mentor=self.request.user.profil_mentor
        ).select_related('eleve', 'matiere')


class NoterSuiviAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if not hasattr(user, 'profil_eleve'):
            return Response({'detail': 'Seuls les élèves peuvent noter un suivi.'}, status=403)
        eleve = user.profil_eleve
        suivi = get_object_or_404(SuiviMentor, pk=pk)
        if suivi.eleve != eleve:
            return Response({'detail': "Vous ne pouvez pas noter le suivi d'un autre élève."}, status=403)

        try:
            note = int(request.data.get('note'))
        except Exception:
            return Response({'detail': 'Note invalide.'}, status=400)

        if not (1 <= note <= 5):
            return Response({'detail': 'La note doit être entre 1 et 5.'}, status=400)

        suivi.note_evaluation = note
        suivi.save()
        serializer = SuiviMentorSerializer(suivi)
        return Response(serializer.data)
