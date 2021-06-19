from django.urls import path

from irrigate import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
]
