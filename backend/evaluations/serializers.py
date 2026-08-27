from rest_framework import serializers
from .models import Examen, Question, Resultat, ReponseEleve, Progression, ExerciceGroupe, HistoriqueProgression
from pedagogie.serializers import MatiereSerializer
from pedagogie.models import Matiere


class ExamenCoursSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    titre = serializers.CharField()


class QuestionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'enonce', 'notion', 'bonne_reponse', 'type_question']


class ExerciceGroupeSerializer(serializers.ModelSerializer):
    etapes = QuestionStepSerializer(many=True, read_only=True)

    class Meta:
        model = ExerciceGroupe
        fields = ['id', 'enonce_principal', 'ordre', 'etapes']


class ExamenSerializer(serializers.ModelSerializer):
    niveau_difficulte = serializers.CharField()
    cours = serializers.SerializerMethodField()
    matiere = serializers.SerializerMethodField()
    editeur_math_effectif = serializers.BooleanField(read_only=True)

    class Meta:
        model = Examen
        fields = ['id', 'titre', 'niveau_difficulte', 'cours', 'matiere', 'date_publication', 'editeur_math', 'editeur_math_effectif']

    def get_cours(self, obj):
        return {'id': obj.cours.id, 'titre': obj.cours.titre}

    def get_matiere(self, obj):
        return {'id': obj.cours.matiere.id, 'nom': obj.cours.matiere.nom}


class ExamenDetailSerializer(ExamenSerializer):
    exercices_groupes = ExerciceGroupeSerializer(many=True, read_only=True, source='exercices_groupes.all')

    class Meta(ExamenSerializer.Meta):
        fields = ExamenSerializer.Meta.fields + ['exercices_groupes']


class QuestionSerializer(serializers.ModelSerializer):
    # Never expose `bonne_reponse` here for students before correction
    class Meta:
        model = Question
        fields = ['id', 'enonce', 'type_question', 'choix_reponses', 'notion']


class QuestionCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'enonce', 'type_question', 'choix_reponses', 'notion', 'bonne_reponse']


class ReponseEleveDetailSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ReponseEleve
        fields = ['id', 'question', 'reponse_donnee', 'correct', 'date_reponse']


class ResultatSerializer(serializers.ModelSerializer):
    eleve = serializers.PrimaryKeyRelatedField(read_only=True)
    examen = ExamenDetailSerializer(read_only=True)
    reponses = serializers.SerializerMethodField()

    class Meta:
        model = Resultat
        fields = ['id', 'eleve', 'examen', 'note', 'date_passage', 'reponses']

    def get_reponses(self, obj):
        reponses = ReponseEleve.objects.filter(eleve=obj.eleve, question__examen=obj.examen).select_related('question').order_by('question__id')
        return ReponseEleveDetailSerializer(reponses, many=True).data


class ProgressionSerializer(serializers.ModelSerializer):
    matiere_nom = serializers.CharField(source='matiere.nom', read_only=True)

    class Meta:
        model = Progression
        fields = ['id', 'matiere', 'matiere_nom', 'niveau_maitrise', 'notions_faibles', 'derniere_mise_a_jour']


class HistoriqueProgressionSerializer(serializers.ModelSerializer):
    matiere_nom = serializers.CharField(source='matiere.nom', read_only=True)

    class Meta:
        model = HistoriqueProgression
        fields = ['id', 'matiere', 'matiere_nom', 'niveau_maitrise', 'date_snapshot']
