from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views import generic

from irrigate.forms import OneOffRunForm
from irrigate.models import ActuatorRunLog, ScheduleTime


class DashboardView(LoginRequiredMixin, generic.ListView):
    template_name = "irrigate/dashboard.html"
    context_object_name = "runs"
    paginate_by = 25

    def get_queryset(self):
        return ActuatorRunLog.objects.select_related("actuator", "schedule_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        running_runs = ActuatorRunLog.objects.select_related(
            "actuator", "schedule_time"
        ).filter(end_datetime__isnull=True)
        completed_schedule_ids = ActuatorRunLog.objects.filter(
            schedule_time_id__isnull=False
        ).values("schedule_time_id")
        queued_one_offs = (
            ScheduleTime.objects.prefetch_related("actuators")
            .filter(
                enabled=True,
                run_type=ScheduleTime.RunType.ONE_OFF,
            )
            .exclude(id__in=completed_schedule_ids)
            .order_by("-id")
        )
        recurring_schedules = list(
            ScheduleTime.objects.prefetch_related("actuators")
            .filter(
                enabled=True,
                run_type=ScheduleTime.RunType.RECURRING,
            )
            .order_by("weekday", "start_time", "id")
        )

        context.update(
            {
                "one_off_form": OneOffRunForm(),
                "running_runs": running_runs,
                "queued_one_offs": queued_one_offs,
                "recurring_schedules": recurring_schedules,
                "recent_run": ActuatorRunLog.objects.select_related(
                    "actuator", "schedule_time"
                ).first(),
                "next_recurring_schedule": self._get_next_recurring_schedule(
                    recurring_schedules
                ),
            }
        )
        return context

    def _get_next_recurring_schedule(self, recurring_schedules):
        if not recurring_schedules:
            return None

        now = timezone.localtime()
        current_weekday = now.weekday()
        current_time = now.time()

        def sort_key(schedule_time):
            days_ahead = (schedule_time.weekday - current_weekday) % 7
            if days_ahead == 0 and schedule_time.start_time <= current_time:
                days_ahead = 7
            return days_ahead, schedule_time.start_time, schedule_time.id

        return min(recurring_schedules, key=sort_key)


class OneOffRunView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        form = OneOffRunForm(request.POST)
        if form.is_valid():
            now = timezone.localtime()
            actuator = form.cleaned_data["actuator"]
            duration_in_minutes = form.cleaned_data["duration_in_minutes"]
            schedule_time = ScheduleTime.objects.create(
                enabled=True,
                run_type=ScheduleTime.RunType.ONE_OFF,
                weekday=now.weekday(),
                start_time=now.time(),
                duration_in_minutes=duration_in_minutes,
            )
            schedule_time.actuators.add(actuator)

            minute_label = "minute" if duration_in_minutes == 1 else "minutes"
            messages.success(
                request,
                f"Queued {actuator.name} for {duration_in_minutes} {minute_label}.",
            )
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)

        return redirect("dashboard")
