from django.urls import path

from .views import DetailCoursView, ListeCoursView

app_name = "pedagogie"

urlpatterns = [
    path("", ListeCoursView.as_view(), name="liste_cours"),
    path("<int:pk>/", DetailCoursView.as_view(), name="detail_cours"),
]