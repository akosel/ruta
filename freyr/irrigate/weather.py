import requests
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

BASE_URL = 'http://api.weatherapi.com/v1'
key = settings.WEATHER_API_KEY
WHERE_I_AM = settings.DEFAULT_WEATHER_LOCATION

def get_current_weather(location=WHERE_I_AM):
    return requests.get(f'{BASE_URL}/current.json', params={'q': location, 'key': key}).json()

def get_forecasted_weather(location=WHERE_I_AM, days=3):
    return requests.get(f'{BASE_URL}/forecast.json', params={'q': location, 'key': key, 'days': days}).json()

def get_historical_weather(location=WHERE_I_AM, days_ago=3):
    now = timezone.now()
    dt = now - timedelta(days=days_ago)
    return requests.get(f'{BASE_URL}/history.json', params={'q': location, 'key': key, 'dt': dt, 'end_dt': now}).json()
