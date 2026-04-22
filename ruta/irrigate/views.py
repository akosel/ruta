from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import generic

from irrigate.forms import OneOffRunForm
from irrigate.models import Actuator, ActuatorRunLog, ScheduleTime
from irrigate.schedule import GRASS_SEED_DURATION_SECONDS, GRASS_SEED_RUN_HOURS


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
        queued_one_offs = list(
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
        now = timezone.localtime()
        for schedule_time in queued_one_offs:
            schedule_time.dashboard_datetime = self._get_schedule_datetime(
                schedule_time,
                now=now,
                future=False,
            )
        for schedule_time in recurring_schedules:
            schedule_time.dashboard_datetime = self._get_schedule_datetime(
                schedule_time,
                now=now,
                future=True,
            )
        actuators = list(Actuator.objects.select_related("device").order_by("name"))
        duration_summaries = {}
        for schedule_time in recurring_schedules:
            schedule_time.duration_details = []
            for actuator in schedule_time.actuators.all():
                summary = None
                if not schedule_time.duration_in_minutes:
                    if actuator.id not in duration_summaries:
                        duration_summaries[
                            actuator.id
                        ] = actuator.get_duration_summary()
                    summary = duration_summaries[actuator.id]
                schedule_time.duration_details.append(
                    {
                        "actuator": actuator,
                        "summary": summary,
                    }
                )

        context.update(
            {
                "actuators": actuators,
                "one_off_form": OneOffRunForm(),
                "running_runs": running_runs,
                "queued_one_offs": queued_one_offs,
                "recurring_schedules": recurring_schedules,
                "grass_seed_enabled_count": sum(
                    1 for actuator in actuators if actuator.grass_seed_mode
                ),
                "grass_seed_run_datetimes": self._get_grass_seed_run_datetimes(now),
                "grass_seed_duration_in_minutes": GRASS_SEED_DURATION_SECONDS / 60,
                "recent_run": ActuatorRunLog.objects.select_related(
                    "actuator", "schedule_time"
                ).first(),
                "next_recurring_schedule": self._get_next_recurring_schedule(
                    recurring_schedules
                ),
            }
        )
        return context

    def _get_schedule_datetime(self, schedule_time, *, now, future):
        days_delta = schedule_time.weekday - now.weekday()
        if future:
            days_delta %= 7

        scheduled_date = now.date() + timedelta(days=days_delta)
        scheduled_datetime = timezone.make_aware(
            datetime.combine(scheduled_date, schedule_time.start_time),
            timezone.get_current_timezone(),
        )

        if future and scheduled_datetime <= now:
            return scheduled_datetime + timedelta(days=7)
        if not future and scheduled_datetime > now:
            return scheduled_datetime - timedelta(days=7)
        return scheduled_datetime

    def _get_grass_seed_run_datetimes(self, now):
        run_datetimes = []
        for hour in GRASS_SEED_RUN_HOURS:
            run_datetime = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if run_datetime <= now:
                run_datetime += timedelta(days=1)
            run_datetimes.append(run_datetime)

        return sorted(run_datetimes)

    def _get_next_recurring_schedule(self, recurring_schedules):
        if not recurring_schedules:
            return None

        return min(
            recurring_schedules,
            key=lambda schedule_time: (
                schedule_time.dashboard_datetime,
                schedule_time.id,
            ),
        )


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


class GrassSeedModeToggleView(LoginRequiredMixin, generic.View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        actuator = get_object_or_404(Actuator, pk=kwargs["pk"])
        actuator.grass_seed_mode = request.POST.get("enabled") == "true"
        actuator.save(update_fields=["grass_seed_mode"])

        status_label = "enabled" if actuator.grass_seed_mode else "disabled"
        messages.success(
            request, f"Grass seed mode {status_label} for {actuator.name}."
        )
        return redirect("dashboard")
