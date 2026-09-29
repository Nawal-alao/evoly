from django.contrib.auth.models import User
from rest_framework import serializers

from pedagogie.models import Matiere

from .models import GroupeEtude, Message, MessagePrive, Signalement


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class MessageSerializer(serializers.ModelSerializer):
    auteur = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'groupe', 'auteur', 'contenu', 'date_envoi', 'statut']
        read_only_fields = ['id', 'auteur', 'date_envoi', 'statut']


class GroupeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupeEtude
        fields = ['id', 'nom', 'classe_scolaire', 'serie', 'matiere']


class GroupeDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(source='messages_groupe', many=True, read_only=True)

    class Meta:
        model = GroupeEtude
        fields = ['id', 'nom', 'classe_scolaire', 'serie', 'matiere', 'messages']


class SignalementSerializer(serializers.ModelSerializer):
    signale_par = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Signalement
        fields = ['id', 'message', 'signale_par', 'motif', 'date_signalement']
        read_only_fields = ['id', 'signale_par', 'date_signalement']


class MessagePriveSerializer(serializers.ModelSerializer):
    auteur = UserSimpleSerializer(read_only=True)

    class Meta:
        model = MessagePrive
        fields = ['id', 'suivi', 'auteur', 'contenu', 'image', 'date_envoi', 'statut', 'lu']
        read_only_fields = ['id', 'auteur', 'date_envoi', 'statut', 'lu']


class SuiviSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    eleve = serializers.CharField()
    mentor = serializers.CharField()
    matiere = serializers.CharField()


class ProposerGroupeSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=150)
    matiere = serializers.PrimaryKeyRelatedField(queryset=Matiere.objects.all())

    def validate_nom(self, value):
        if GroupeEtude.objects.filter(nom__iexact=value.strip()).exists():
            raise serializers.ValidationError("Un groupe avec ce nom existe déjà.")
        return value.strip()
