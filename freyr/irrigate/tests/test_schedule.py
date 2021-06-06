from datetime import time
from unittest.mock import Mock, patch

from django.test import TestCase
from freezegun import freeze_time

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime
from irrigate.schedule import run_all


class ScheduleTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(name='device')
        self.actuator = Actuator.objects.create(name='test', gpio_pin=5, device=self.device)

    @patch('irrigate.models.Actuator.get_temperature_watering_adjustment_multiplier')
    @patch('irrigate.models.Actuator.get_duration_in_seconds')
    @patch('irrigate.schedule.time.sleep')
    def test_run_all(self, mock_sleep, mock_get_duration_in_seconds, mock_get_temperature_watering_adjustment_multiplier):
        mock_get_temperature_watering_adjustment_multiplier.return_value = 1
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

    @patch('irrigate.models.Actuator.get_temperature_watering_adjustment_multiplier')
    @patch('irrigate.models.Actuator.get_duration_in_seconds')
    @patch('irrigate.schedule.time.sleep')
    def test_run_all_multiple(self, mock_sleep, mock_get_duration_in_seconds, mock_get_temperature_watering_adjustment_multiplier):
        mock_get_temperature_watering_adjustment_multiplier.return_value = 1
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
