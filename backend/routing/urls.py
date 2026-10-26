from django.urls import path

from .views import HealthView, HeatmapView, PlanView

urlpatterns = [
    path("plan", PlanView.as_view()),
    path("heatmap", HeatmapView.as_view()),
    path("health", HealthView.as_view()),
]
