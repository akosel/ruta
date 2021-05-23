import requests
from datetime import datetime, timedelta

WHERE_I_AM = 'Ann Arbor'
BASE_URL = 'http://api.weatherapi.com/v1'
key = 'a93ec7cf4a7341358e004153211605'

def get_current_weather(location=WHERE_I_AM):
    return requests.get(f'{BASE_URL}/current.json', params={'q': location, 'key': key}).json()

def get_forecasted_weather(location=WHERE_I_AM, days=3):
    return requests.get(f'{BASE_URL}/forecast.json', params={'q': location, 'key': key, 'days': days}).json()

def get_historical_weather(location=WHERE_I_AM, days_ago=3):
    dt = datetime.now() - timedelta(days=days_ago)
    return requests.get(f'{BASE_URL}/history.json', params={'q': location, 'key': key, 'dt': dt, 'end_dt': datetime.now()}).json()
