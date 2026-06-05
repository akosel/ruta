import logging
from enum import Enum
from dataclasses import asdict, dataclass
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

BASE_URL = settings.MONITORING_WEBHOOK_URL
REQUEST_TIMEOUT = (5, 15)

logger = logging.getLogger(__name__)


class MonitoringEventStatus(Enum):
    IN_PROGRESS = "in progress"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class MonitoringEvent:
    name: str
    status: MonitoringEventStatus
    created_at: datetime = timezone.now()


def emit(event_data: MonitoringEvent):
    try:
        response = requests.post(
            BASE_URL,
            data=asdict(event_data),
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.warning("Error emitting monitoring event: %s", e)
        return None
    return response
