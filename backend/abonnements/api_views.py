from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Abonnement
from .serializers import AbonnementSerializer


class MonAbonnementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        eleve = request.user.profil_eleve
        actif = eleve.abonnements.filter(statut=Abonnement.Statut.ACTIF).first()
        historique = eleve.abonnements.exclude(statut=Abonnement.Statut.ACTIF)
        data = {
            'abonnement_actif': AbonnementSerializer(actif).data if actif else None,
            'historique': AbonnementSerializer(historique, many=True).data,
        }
        return Response(data)


class SouscrireAbonnementAPIView(generics.CreateAPIView):
    serializer_class = AbonnementSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # always link to request.user.profil_eleve
        eleve = self.request.user.profil_eleve
        serializer.save(eleve=eleve)


class AnnulerAbonnementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        eleve = request.user.profil_eleve
        abonnement = get_object_or_404(Abonnement, eleve=eleve, statut=Abonnement.Statut.ACTIF)
        abonnement.statut = Abonnement.Statut.ANNULE
        abonnement.save()
        return Response({'detail': 'Abonnement annulé.'})
