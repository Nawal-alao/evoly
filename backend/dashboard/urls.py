from django.urls import path

from .views import AccueilView, DashboardEleveView, DashboardMentorView

app_name = "dashboard"

urlpatterns = [
    path("", AccueilView.as_view(), name="accueil"),
    path("eleve/", DashboardEleveView.as_view(), name="dashboard_eleve"),
    path("mentor/", DashboardMentorView.as_view(), name="dashboard_mentor"),
]
