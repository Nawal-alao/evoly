from rest_framework import serializers

from .models import Cours, Matiere, Sequence


class MatiereSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matiere
        fields = ['id', 'nom', 'description']


class SequenceSerializer(serializers.ModelSerializer):
    # NOTE for frontend: `contenu` contains rich HTML. The frontend must
    # sanitize or render it safely (e.g. using a trusted HTML renderer) and
    # must NOT blindly use React's `dangerouslySetInnerHTML` without
    # validating/sanitizing the content first.
    contenu = serializers.CharField()

    class Meta:
        model = Sequence
        fields = ['id', 'titre', 'ordre', 'contenu']


class CoursSerializer(serializers.ModelSerializer):
    sequences = SequenceSerializer(many=True, read_only=True)
    termine = serializers.SerializerMethodField()
    favori = serializers.SerializerMethodField()

    class Meta:
        model = Cours
        fields = [
            'id', 'titre', 'description', 'matiere', 'classe_scolaire', 'serie',
            'contenu', 'statut_validation', 'sequences', 'termine', 'favori',
        ]
        read_only_fields = ['id', 'statut_validation', 'sequences', 'termine', 'favori']

    def get_termine(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profil_eleve'):
            return False
        return obj.termine_par.filter(eleve=request.user.profil_eleve).exists()

    def get_favori(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profil_eleve'):
            return False
        return obj.favori_par.filter(eleve=request.user.profil_eleve).exists()
