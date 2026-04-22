from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime


class DashboardAuthTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_one_off_run_requires_login(self):
        response = self.client.post(reverse("one_off_run"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('one_off_run')}"
        )

    def test_dashboard_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="ruta", password="correct-password"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irrigate/dashboard.html")

    def test_login_redirects_authenticated_user_to_dashboard(self):
        get_user_model().objects.create_user(
            username="ruta", password="correct-password"
        )

        response = self.client.post(
            reverse("login"),
            {"username": "ruta", "password": "correct-password"},
        )

        self.assertRedirects(response, reverse("dashboard"))


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ruta", password="correct-password"
        )
        self.client.force_login(self.user)
        self.device = Device.objects.create(name="device")
        self.actuator = Actuator.objects.create(
            name="Front Yard", gpio_pin=5, device=self.device
        )

    def test_dashboard_includes_schedule_queue_and_paginated_runs(self):
        recurring_schedule = ScheduleTime.objects.create(
            run_type=ScheduleTime.RunType.RECURRING,
            weekday=ScheduleTime.Weekday.MONDAY,
            start_time=time(6, 0),
        )
        recurring_schedule.actuators.add(self.actuator)
        queued_one_off = ScheduleTime.objects.create(
            run_type=ScheduleTime.RunType.ONE_OFF,
            weekday=ScheduleTime.Weekday.MONDAY,
            start_time=time(7, 0),
            duration_in_minutes=10,
        )
        queued_one_off.actuators.add(self.actuator)

        now = timezone.now()
        for index in range(30):
            start_datetime = now - timedelta(minutes=index)
            ActuatorRunLog.objects.create(
                actuator=self.actuator,
                start_datetime=start_datetime,
                end_datetime=start_datetime + timedelta(minutes=5),
            )

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["recurring_schedules"]), [recurring_schedule]
        )
        self.assertEqual(list(response.context["queued_one_offs"]), [queued_one_off])
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["runs"]), 25)
        self.assertContains(response, "Front Yard")
        self.assertContains(response, "Queued one-off runs")
        self.assertContains(response, "Schedule")
        self.assertContains(response, "Page 1 of 2")

    def test_dashboard_excludes_one_offs_that_already_have_a_run(self):
        completed_one_off = ScheduleTime.objects.create(
            run_type=ScheduleTime.RunType.ONE_OFF,
            weekday=ScheduleTime.Weekday.MONDAY,
            start_time=time(7, 0),
            duration_in_minutes=10,
        )
        completed_one_off.actuators.add(self.actuator)
        ActuatorRunLog.objects.create(
            actuator=self.actuator,
            schedule_time=completed_one_off,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(minutes=10),
        )

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(list(response.context["queued_one_offs"]), [])

    @freeze_time("2021-05-31 09:55:00+00:00")
    def test_dashboard_includes_browser_timezone_datetime_markup(self):
        recurring_schedule = ScheduleTime.objects.create(
            run_type=ScheduleTime.RunType.RECURRING,
            weekday=ScheduleTime.Weekday.MONDAY,
            start_time=time(10, 0),
        )
        recurring_schedule.actuators.add(self.actuator)
        start_datetime = timezone.make_aware(datetime(2021, 5, 31, 10, 30))
        ActuatorRunLog.objects.create(
            actuator=self.actuator,
            start_datetime=start_datetime,
            end_datetime=start_datetime + timedelta(minutes=5),
        )

        response = self.client.get(reverse("dashboard"))

        schedule = response.context["recurring_schedules"][0]
        self.assertEqual(
            schedule.dashboard_datetime.isoformat(), "2021-05-31T10:00:00+00:00"
        )
        self.assertContains(response, "irrigate/js/dashboard.js")
        self.assertContains(response, 'datetime="2021-05-31T10:30:00+00:00"')
        self.assertContains(response, 'data-dashboard-format="datetime"')
        self.assertContains(response, 'data-dashboard-format="weekday"')
        self.assertContains(response, 'data-dashboard-format="time"')

    def test_one_off_run_post_creates_queued_schedule(self):
        response = self.client.post(
            reverse("one_off_run"),
            {
                "actuator": self.actuator.id,
                "duration_in_minutes": 12,
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        schedule_time = ScheduleTime.objects.get(run_type=ScheduleTime.RunType.ONE_OFF)
        self.assertTrue(schedule_time.enabled)
        self.assertEqual(schedule_time.duration_in_minutes, 12)
        self.assertEqual(schedule_time.actuators.get(), self.actuator)

    def test_one_off_run_rejects_invalid_duration(self):
        response = self.client.post(
            reverse("one_off_run"),
            {
                "actuator": self.actuator.id,
                "duration_in_minutes": 121,
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(
            ScheduleTime.objects.filter(run_type=ScheduleTime.RunType.ONE_OFF).exists()
        )

    def test_one_off_run_rejects_running_actuator(self):
        ActuatorRunLog.objects.create(
            actuator=self.actuator,
            start_datetime=timezone.now(),
        )

        response = self.client.post(
            reverse("one_off_run"),
            {
                "actuator": self.actuator.id,
                "duration_in_minutes": 10,
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(
            ScheduleTime.objects.filter(run_type=ScheduleTime.RunType.ONE_OFF).exists()
        )
