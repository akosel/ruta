from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from irrigate.monitor import (
    BASE_URL,
    REQUEST_TIMEOUT,
    MonitoringEvent,
    MonitoringEventStatus,
    emit,
)


class MonitorTests(SimpleTestCase):
    @patch("irrigate.monitor.requests.post")
    def test_emit_uses_request_timeout(self, mock_post):
        event = MonitoringEvent(
            name="test event",
            status=MonitoringEventStatus.IN_PROGRESS,
        )

        emit(event)

        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs["timeout"], REQUEST_TIMEOUT)
        self.assertEqual(mock_post.call_args.args[0], BASE_URL)

    @patch("irrigate.monitor.requests.post")
    def test_emit_returns_when_request_times_out(self, mock_post):
        mock_post.side_effect = requests.Timeout("timed out")
        event = MonitoringEvent(
            name="test event",
            status=MonitoringEventStatus.IN_PROGRESS,
        )

        response = emit(event)

        self.assertIsNone(response)
