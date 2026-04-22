from django.urls import path

from irrigate import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("runs/one-off/", views.OneOffRunView.as_view(), name="one_off_run"),
]
