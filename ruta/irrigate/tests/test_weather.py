from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from irrigate.weather import (
    REQUEST_TIMEOUT,
    get_current_weather,
    get_forecasted_weather,
    get_historical_weather,
)


class WeatherTests(SimpleTestCase):
    def setUp(self):
        self.response = Mock()
        self.response.json.return_value = {"weather": "data"}

    @patch("irrigate.weather.requests.get")
    def test_current_weather_uses_request_timeout(self, mock_get):
        mock_get.return_value = self.response

        get_current_weather()

        self.assertEqual(mock_get.call_args.kwargs["timeout"], REQUEST_TIMEOUT)

    @patch("irrigate.weather.requests.get")
    def test_forecasted_weather_uses_request_timeout(self, mock_get):
        mock_get.return_value = self.response

        get_forecasted_weather()

        self.assertEqual(mock_get.call_args.kwargs["timeout"], REQUEST_TIMEOUT)

    @patch("irrigate.weather.requests.get")
    def test_historical_weather_uses_request_timeout(self, mock_get):
        mock_get.return_value = self.response

        get_historical_weather()

        self.assertEqual(mock_get.call_args.kwargs["timeout"], REQUEST_TIMEOUT)
