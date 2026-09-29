from django.contrib.auth.models import User
from rest_framework import serializers

from pedagogie.models import Matiere

from .models import Eleve, Mentor, SuiviMentor


class EleveSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='utilisateur.username')

    class Meta:
        model = Eleve
        fields = [
            'id', 'username', 'prenom', 'nom', 'age', 'classe_scolaire', 'serie', 'date_inscription',
        ]
        read_only_fields = ['id', 'username', 'date_inscription']


class MatiereSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matiere
        fields = ['id', 'nom']


class MentorSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='utilisateur.username')
    matieres = serializers.PrimaryKeyRelatedField(queryset=Matiere.objects.all(), many=True)
    matieres_detail = MatiereSimpleSerializer(source='matieres', many=True, read_only=True)
    note_moyenne = serializers.ReadOnlyField()

    class Meta:
        model = Mentor
        fields = ['id', 'username', 'prenom', 'nom', 'bio', 'matieres', 'matieres_detail', 'disponible', 'note_moyenne']
        read_only_fields = ['id', 'username', 'matieres_detail', 'note_moyenne']


class SuiviMentorSerializer(serializers.ModelSerializer):
    eleve_name = serializers.SerializerMethodField(read_only=True)
    mentor_name = serializers.SerializerMethodField(read_only=True)
    matiere_nom = serializers.CharField(source='matiere.nom', read_only=True)

    class Meta:
        model = SuiviMentor
        fields = [
            'id', 'eleve', 'eleve_name', 'mentor', 'mentor_name',
            'matiere', 'matiere_nom', 'date_debut', 'actif', 'note_evaluation',
        ]
        read_only_fields = ['id', 'date_debut']

    def get_eleve_name(self, obj):
        return f"{obj.eleve.prenom} {obj.eleve.nom}"

    def get_mentor_name(self, obj):
        return f"{obj.mentor.prenom} {obj.mentor.nom}"


class InscriptionEleveSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Eleve
        fields = ['id', 'username', 'password', 'prenom', 'nom', 'age', 'classe_scolaire', 'serie']
        read_only_fields = ['id']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        user = User.objects.create_user(username=username, password=password)
        eleve = Eleve.objects.create(utilisateur=user, **validated_data)
        return eleve


class InscriptionMentorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    matieres = serializers.PrimaryKeyRelatedField(queryset=Matiere.objects.all(), many=True)

    class Meta:
        model = Mentor
        fields = ['id', 'username', 'password', 'prenom', 'nom', 'bio', 'matieres']
        read_only_fields = ['id']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        matieres = validated_data.pop('matieres', [])
        user = User.objects.create_user(username=username, password=password)
        mentor = Mentor.objects.create(utilisateur=user, **validated_data)
        mentor.matieres.set(matieres)
        return mentor
