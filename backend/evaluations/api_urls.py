from django.urls import path
from . import api_views

urlpatterns = [
    path('examens/', api_views.ExamensListAPIView.as_view(), name='api_examens_list'),
    path('examens/<int:pk>/passer/', api_views.PasserExamenAPIView.as_view(), name='api_passer_examen'),
    path('examens/<int:pk>/soumettre/', api_views.SoumettreExamenAPIView.as_view(), name='api_soumettre_examen'),
    path('resultats/<int:pk>/', api_views.ResultatDetailAPIView.as_view(), name='api_resultat_detail'),
    path('progressions/', api_views.MesProgressionsAPIView.as_view(), name='api_mes_progressions'),
    path('progression/historique/', api_views.HistoriqueProgressionAPIView.as_view(), name='api_historique_progression'),
]
