from datetime import datetime, time, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime


class ActuatorTests(TestCase):
    def setUp(self):
        device = Device.objects.create(name="device")
        self.actuator = Actuator.objects.create(name="test", gpio_pin=5, device=device)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        self.actuator.get_precipitation_from_rain_in_inches = Mock(return_value=0)
        self.actuator.get_forecasted_precipitation_from_rain_in_inches = Mock(
            return_value=0
        )

    def test_get_duration_in_seconds(self):
        self.actuator.get_recent_water_amount_in_inches = Mock(return_value=0.67)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        duration_in_seconds = self.actuator.get_duration_in_seconds()
        self.assertEqual(
            duration_in_seconds, ((1 - 0.67) / self.actuator.flow_rate_per_minute) * 60
        )

    def test_get_duration_in_seconds_skip_watering(self):
        self.actuator.get_recent_water_amount_in_inches = Mock(return_value=0.9)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        duration_in_seconds = self.actuator.get_duration_in_seconds()
        self.assertEqual(duration_in_seconds, 0)

    def test_get_duration_in_seconds_respect_baseline(self):
        self.actuator.get_recent_water_amount_in_inches = Mock(return_value=0)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        self.actuator.get_precipitation_from_rain_in_inches = Mock(return_value=0)
        self.actuator.get_forecasted_precipitation_from_rain_in_inches = Mock(
            return_value=0
        )
        duration_in_seconds = self.actuator.get_duration_in_seconds()
        self.assertEqual(
            duration_in_seconds,
            self.actuator.duration_in_minutes_per_scheduled_day * 60,
        )

    def test_get_duration_in_seconds_account_for_rain(self):
        self.actuator.get_recent_water_amount_in_inches = Mock(return_value=0.42)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        self.actuator.get_precipitation_from_rain_in_inches = Mock(return_value=0.25)
        duration_in_seconds = self.actuator.get_duration_in_seconds()
        self.assertEqual(
            round(duration_in_seconds),
            round(((1 - 0.67) / self.actuator.flow_rate_per_minute) * 60),
        )

    def test_get_recent_water_amount_in_inches(self):
        for i in range(3):
            start_datetime = timezone.now() - timedelta(days=i + 1)
            end_datetime = start_datetime + timedelta(minutes=12)
            ActuatorRunLog.objects.create(
                actuator=self.actuator,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

        amount = self.actuator.get_recent_water_amount_in_inches(days_ago=7)

        self.assertEqual(amount, (12 * 3 * self.actuator.flow_rate_per_minute))

    def test_get_recent_water_amount_in_inches_too_old(self):
        for i in range(3):
            start_datetime = timezone.now() - timedelta(days=i + 3)
            end_datetime = start_datetime + timedelta(minutes=12)
            ActuatorRunLog.objects.create(
                actuator=self.actuator,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

        amount = self.actuator.get_recent_water_amount_in_inches(days_ago=1)

        self.assertEqual(amount, 0)

    def test_get_recent_water_amount_in_inches_missing_end_datetime(self):
        for i in range(3):
            start_datetime = timezone.now() - timedelta(days=i + 1)
            ActuatorRunLog.objects.create(
                actuator=self.actuator, start_datetime=start_datetime
            )

        amount = self.actuator.get_recent_water_amount_in_inches(days_ago=7)

        self.assertEqual(amount, 0)

    def test_get_number_of_scheduled_times(self):
        for i in range(3):
            start_time = time(6, 0)
            schedule_time = ScheduleTime.objects.create(
                weekday=i, start_time=start_time
            )
            schedule_time.actuators.add(self.actuator)

        count = self.actuator.get_number_of_scheduled_times()

        self.assertEqual(count, 3)
