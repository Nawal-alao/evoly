from django.urls import path
from . import api_views

urlpatterns = [
    path('matieres/', api_views.MatiereListAPIView.as_view(), name='api_matieres_list'),
    path('cours/', api_views.CoursListAPIView.as_view(), name='api_cours_list'),
    path('cours/favoris/', api_views.CoursFavorisListAPIView.as_view(), name='api_cours_favoris_list'),
    path('cours/derriere-activite/', api_views.DerniereActiviteAPIView.as_view(), name='api_cours_derriere_activite'),
    path('cours/<int:pk>/', api_views.CoursDetailAPIView.as_view(), name='api_cours_detail'),
    path('cours/<int:pk>/terminer/', api_views.MarquerCoursTermineAPIView.as_view(), name='api_cours_terminer'),
    path('cours/<int:pk>/favori/', api_views.AjouterAuxFavorisAPIView.as_view(), name='api_cours_favori_toggle'),
    path('cours/<int:pk>/progression/', api_views.CoursProgressionAPIView.as_view(), name='api_cours_progression'),
]
