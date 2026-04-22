from django.urls import path

from irrigate import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path(
        "actuators/<int:pk>/grass-seed-mode/",
        views.GrassSeedModeToggleView.as_view(),
        name="grass_seed_mode_toggle",
    ),
    path("runs/one-off/", views.OneOffRunView.as_view(), name="one_off_run"),
]
