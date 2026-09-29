from django.urls import path

from . import api_views

urlpatterns = [
    path('inscription/eleve/', api_views.InscriptionEleveAPIView.as_view(), name='api_inscription_eleve'),
    path('inscription/mentor/', api_views.InscriptionMentorAPIView.as_view(), name='api_inscription_mentor'),
    path('mon-profil/', api_views.MonProfilAPIView.as_view(), name='api_mon_profil'),
    path('mes-suivis/', api_views.MesSuivisAPIView.as_view(), name='api_mes_suivis'),
    path('suivis-mentor/', api_views.SuivisMentorAPIView.as_view(), name='api_suivis_mentor'),
    path('mentors/', api_views.ListeMentorsAPIView.as_view(), name='api_liste_mentors'),
    path('mentors/<int:pk>/suivre/', api_views.SuivreMentorAPIView.as_view(), name='api_suivre_mentor'),
    path('suivis/<int:pk>/noter/', api_views.NoterSuiviAPIView.as_view(), name='api_noter_suivi'),
]
