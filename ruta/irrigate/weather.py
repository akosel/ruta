import requests
from datetime import timedelta

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

BASE_URL = 'http://api.weatherapi.com/v1'
key = settings.WEATHER_API_KEY
WHERE_I_AM = settings.DEFAULT_WEATHER_LOCATION

def cache_response(func):
    def wrapper(*args, **kwargs):
        kwargs_hash = hash(frozenset(kwargs.items()))
        key = f'{func.__name__}-{args}-{kwargs_hash}-{timezone.now().date()}'
        if cache.get(key):
            return cache.get(key)
        data = func(*args, **kwargs)
        cache.set(key, data, timeout=60 * 60)
        return data
    return wrapper

def get_current_weather(location=WHERE_I_AM):
    return requests.get(f'{BASE_URL}/current.json', params={'q': location, 'key': key}).json()

@cache_response
def get_forecasted_weather(location=WHERE_I_AM, days=3):
    return requests.get(f'{BASE_URL}/forecast.json', params={'q': location, 'key': key, 'days': days}).json()

@cache_response
def get_historical_weather(location=WHERE_I_AM, days_ago=3):
    now = timezone.now()
    dt = now - timedelta(days=days_ago)
    return requests.get(f'{BASE_URL}/history.json', params={'q': location, 'key': key, 'dt': dt, 'end_dt': now}).json()
