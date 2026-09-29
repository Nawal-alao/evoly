from rest_framework import serializers

from .models import Abonnement


class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abonnement
        fields = ['id', 'eleve', 'formule', 'statut', 'date_debut', 'date_fin']
        read_only_fields = ['id', 'statut', 'date_debut']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # include eleve id and optional display
        rep['eleve'] = instance.eleve.id
        return rep
