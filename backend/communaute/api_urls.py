from django.urls import path

from . import api_views

urlpatterns = [
    path('groupes/', api_views.GroupesListAPIView.as_view(), name='api_groupes_list'),
    path('groupes/proposer/', api_views.ProposerGroupeAPIView.as_view(), name='api_groupe_proposer'),
    path('groupes/<int:pk>/', api_views.GroupeDetailAPIView.as_view(), name='api_groupe_detail'),
    path('groupes/<int:pk>/envoyer/', api_views.EnvoyerMessageAPIView.as_view(), name='api_groupe_envoyer'),

    path('messages/<int:pk>/signaler/', api_views.SignalerMessageAPIView.as_view(), name='api_message_signaler'),

    path('conversations/', api_views.ConversationsListAPIView.as_view(), name='api_conversations_list'),
    path('conversations/<int:pk>/', api_views.ConversationDetailAPIView.as_view(), name='api_conversation_detail'),
    path(
        'conversations/<int:pk>/envoyer/',
        api_views.EnvoyerMessagePriveAPIView.as_view(),
        name='api_conversation_envoyer',
    ),
]
