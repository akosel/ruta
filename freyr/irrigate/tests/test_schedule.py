from unittest.mock import Mock, patch

from django.test import TestCase
from irrigate.models import Actuator, ActuatorRunLog, Device
from irrigate.schedule import get_duration_in_seconds


class ScheduleTests(TestCase):
    def setUp(self):
        device = Device.objects.create(name='device')
        self.actuator = Actuator.objects.create(name='test', gpio_pin=5, device=device)

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
