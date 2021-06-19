from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic

from irrigate.models import ActuatorRunLog


class DashboardView(generic.ListView):
    template_name = "irrigate/dashboard.html"
    context_object_name = "runs"

    def get_queryset(self):
        return ActuatorRunLog.objects.all()
