from datetime import time
from unittest.mock import Mock, patch

from django.test import TestCase
from freezegun import freeze_time

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime
from irrigate.schedule import get_duration_in_seconds, run_all


class ScheduleTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(name='device')
        self.actuator = Actuator.objects.create(name='test', gpio_pin=5, device=self.device)

    @patch('irrigate.schedule.get_precipitation_from_rain_in_inches')
    def test_get_duration_in_seconds(self, mock_get_precipitation_from_rain_in_inches):
        self.actuator.get_recent_water_amount_in_minutes = Mock(return_value=.67)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        mock_get_precipitation_from_rain_in_inches.return_value = 0
        duration_in_seconds = get_duration_in_seconds(self.actuator)
        self.assertEqual(duration_in_seconds, ((1 - .67) / self.actuator.flow_rate_per_minute) * 60)

    @patch('irrigate.schedule.get_precipitation_from_rain_in_inches')
    def test_get_duration_in_seconds_skip_watering(self, mock_get_precipitation_from_rain_in_inches):
        self.actuator.get_recent_water_amount_in_minutes = Mock(return_value=.9)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        mock_get_precipitation_from_rain_in_inches.return_value = 0
        duration_in_seconds = get_duration_in_seconds(self.actuator)
        self.assertEqual(duration_in_seconds, 0)

    @patch('irrigate.schedule.get_precipitation_from_rain_in_inches')
    def test_get_duration_in_seconds_respect_baseline(self, mock_get_precipitation_from_rain_in_inches):
        self.actuator.get_recent_water_amount_in_minutes = Mock(return_value=0)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        mock_get_precipitation_from_rain_in_inches.return_value = 0
        duration_in_seconds = get_duration_in_seconds(self.actuator)
        self.assertEqual(duration_in_seconds, self.actuator.duration_in_minutes_per_scheduled_day * 60)

    @patch('irrigate.schedule.get_precipitation_from_rain_in_inches')
    def test_get_duration_in_seconds_account_for_rain(self, mock_get_precipitation_from_rain_in_inches):
        self.actuator.get_recent_water_amount_in_minutes = Mock(return_value=.42)
        self.actuator.get_number_of_scheduled_times = Mock(return_value=3)
        mock_get_precipitation_from_rain_in_inches.return_value = .25
        duration_in_seconds = get_duration_in_seconds(self.actuator)
        self.assertEqual(round(duration_in_seconds), round(((1 - .67) / self.actuator.flow_rate_per_minute) * 60))

    @patch('irrigate.schedule.get_duration_in_seconds')
    @patch('irrigate.schedule.time.sleep')
    def test_run_all(self, mock_sleep, mock_get_duration_in_seconds):
        schedule_time = ScheduleTime.objects.create(weekday=0, start_time=time(10, 0))
        schedule_time.actuators.add(self.actuator)
        SPRINKLER_DURATION = 720
        mock_get_duration_in_seconds.return_value = SPRINKLER_DURATION
        with freeze_time('2021-05-31 9:55'):
            run_all()
            mock_sleep.assert_not_called()

        with freeze_time('2021-05-31 10:01'):
            run_all()
            mock_sleep.assert_called_once_with(SPRINKLER_DURATION)

        mock_sleep.reset_mock()
        with freeze_time('2021-05-31 11:00'):
            run_all()
            mock_sleep.assert_not_called()

    @patch('irrigate.schedule.get_duration_in_seconds')
    @patch('irrigate.schedule.time.sleep')
    def test_run_all_multiple(self, mock_sleep, mock_get_duration_in_seconds):
        schedule_time = ScheduleTime.objects.create(weekday=0, start_time=time(10, 0))
        another_actuator = Actuator.objects.create(name='test', gpio_pin=6, device=self.device)
        schedule_time.actuators.add(self.actuator, another_actuator)
        SPRINKLER_DURATION = 720
        mock_get_duration_in_seconds.return_value = SPRINKLER_DURATION
        with freeze_time('2021-05-31 9:55'):
            run_all()
            mock_sleep.assert_not_called()

        with freeze_time('2021-05-31 10:01'):
            run_all()
            self.assertEqual(mock_sleep.call_count, 2)

        mock_sleep.reset_mock()
        with freeze_time('2021-05-31 11:00'):
            run_all()
            mock_sleep.assert_not_called()

    @patch('irrigate.schedule._run')
    def test_run_all_no_times(self, mock_run):
        run_all()
        mock_run.assert_not_called()
