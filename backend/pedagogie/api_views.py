from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Max

from .models import Matiere, Cours, CoursTermine, CoursFavori, CoursProgression
from .serializers import MatiereSerializer, CoursSerializer
from .views import _cours_de_lutilisateur


class MatiereListAPIView(generics.ListAPIView):
    serializer_class = MatiereSerializer
    permission_classes = [AllowAny]
    queryset = Matiere.objects.all().order_by('nom')


class CoursListAPIView(generics.ListAPIView):
    serializer_class = CoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _cours_de_lutilisateur(self.request.user)


class CoursDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure the object is only retrievable if in the allowed queryset
        return _cours_de_lutilisateur(self.request.user)


class MarquerCoursTermineAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        eleve = getattr(request.user, 'profil_eleve', None)
        if not eleve:
            return Response(
                {"detail": "Seuls les élèves peuvent marquer un cours comme terminé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cours = get_object_or_404(
            _cours_de_lutilisateur(request.user), pk=pk
        )

        termine, created = CoursTermine.objects.get_or_create(
            eleve=eleve, cours=cours
        )
        if not created:
            termine.delete()
            return Response({"termine": False}, status=status.HTTP_200_OK)

        return Response({"termine": True}, status=status.HTTP_201_CREATED)


class AjouterAuxFavorisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        eleve = getattr(request.user, 'profil_eleve', None)
        if not eleve:
            return Response(
                {"detail": "Seuls les élèves peuvent ajouter des cours en favoris."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cours = get_object_or_404(
            _cours_de_lutilisateur(request.user), pk=pk
        )

        favori, created = CoursFavori.objects.get_or_create(
            eleve=eleve, cours=cours
        )
        if not created:
            favori.delete()
            return Response({"favori": False}, status=status.HTTP_200_OK)

        return Response({"favori": True}, status=status.HTTP_201_CREATED)


class CoursFavorisListAPIView(generics.ListAPIView):
    serializer_class = CoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        eleve = getattr(self.request.user, 'profil_eleve', None)
        if not eleve:
            return Cours.objects.none()
        return Cours.objects.filter(
            favori_par__eleve=eleve,
            statut_validation="VALIDE",
        )


class CoursProgressionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_eleve(self, request):
        eleve = getattr(request.user, 'profil_eleve', None)
        if not eleve:
            return None
        return eleve

    def get(self, request, pk):
        eleve = self._get_eleve(request)
        if not eleve:
            return Response(
                {"detail": "Seuls les élèves ont une progression."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cours = get_object_or_404(
            _cours_de_lutilisateur(request.user), pk=pk
        )

        progression = CoursProgression.objects.filter(
            eleve=eleve, cours=cours
        ).first()

        if not progression or not progression.derniere_sequence:
            return Response({"sequence_id": None})

        return Response({
            "sequence_id": progression.derniere_sequence.id,
            "ordre": progression.derniere_sequence.ordre,
            "titre_sequence": progression.derniere_sequence.titre,
            "date_mise_a_jour": progression.date_mise_a_jour,
        })

    def post(self, request, pk):
        eleve = self._get_eleve(request)
        if not eleve:
            return Response(
                {"detail": "Seuls les élèves peuvent enregistrer une progression."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cours = get_object_or_404(
            _cours_de_lutilisateur(request.user), pk=pk
        )

        sequence_id = request.data.get("sequence_id")
        if not sequence_id:
            return Response(
                {"detail": "sequence_id est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sequence = cours.sequences.filter(id=sequence_id).first()
        if not sequence:
            return Response(
                {"detail": "Séquence invalide pour ce cours."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progression, _ = CoursProgression.objects.update_or_create(
            eleve=eleve,
            cours=cours,
            defaults={"derniere_sequence": sequence},
        )

        return Response({
            "sequence_id": progression.derniere_sequence.id,
            "date_mise_a_jour": progression.date_mise_a_jour,
        }, status=status.HTTP_200_OK)


class DerniereActiviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        eleve = getattr(request.user, 'profil_eleve', None)
        if not eleve:
            return Response(
                {"detail": "Seuls les élèves ont une activité de lecture."},
                status=status.HTTP_403_FORBIDDEN,
            )

        progression = (
            CoursProgression.objects
            .filter(eleve=eleve, derniere_sequence__isnull=False)
            .select_related('cours', 'derniere_sequence', 'cours__matiere')
            .order_by('-date_mise_a_jour')
            .first()
        )

        if not progression:
            return Response({})

        return Response({
            "cours_id": progression.cours.id,
            "titre": progression.cours.titre,
            "matiere_nom": progression.cours.matiere.nom,
            "sequence_id": progression.derniere_sequence.id,
            "ordre": progression.derniere_sequence.ordre,
            "titre_sequence": progression.derniere_sequence.titre,
        })
