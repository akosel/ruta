from django.urls import path

from irrigate import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
