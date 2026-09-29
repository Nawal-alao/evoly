from django.urls import path

from .views import (
    DetailConversationView,
    DetailGroupeView,
    EnvoyerMessagePriveView,
    EnvoyerMessageView,
    ListeConversationsView,
    ListeGroupesView,
    SignalerMessageView,
)

app_name = "communaute"

urlpatterns = [
    path("groupes/", ListeGroupesView.as_view(), name="liste_groupes"),
    path("groupes/<int:pk>/", DetailGroupeView.as_view(), name="detail_groupe"),
    path("groupes/<int:pk>/envoyer-message/", EnvoyerMessageView.as_view(), name="envoyer_message"),
    path("messages/<int:pk>/signaler/", SignalerMessageView.as_view(), name="signaler_message"),
    path("conversations/", ListeConversationsView.as_view(), name="liste_conversations"),
    path("conversations/<int:pk>/", DetailConversationView.as_view(), name="detail_conversation"),
    path("conversations/<int:pk>/envoyer/", EnvoyerMessagePriveView.as_view(), name="envoyer_message_prive"),
]
