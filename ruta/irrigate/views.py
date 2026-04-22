from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from irrigate.models import ActuatorRunLog


class DashboardView(LoginRequiredMixin, generic.ListView):
    template_name = "irrigate/dashboard.html"
    context_object_name = "runs"

    def get_queryset(self):
        return ActuatorRunLog.objects.all()[:100]
