from enum import Enum
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone

BASE_URL = settings.MONITORING_WEBHOOK_URL

class MonitoringEventStatus(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'

@dataclass
class MonitoringEvent:
    name: str
    status: MonitoringEventStatus
    created_at: datetime = timezone.now()

def emit(event_data: MonitoringEvent):
    return requests.post(BASE_URL, data=asdict(event_data))
