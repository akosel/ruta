from irrigate.constants import MINIMUM_WATER_DURATION_IN_SECONDS, SKIP_WATERING_THRESHOLD_IN_SECONDS
from irrigate.models import Actuator, ActuatorRun, ScheduleTime
from irrigate.weather import get_forecasted_weather, get_historical_weather

def get_precipitation_from_rain_in_inches(self, days_ago=7):
    """
    Get the amount of precipitation that has fallen.
    """
    data = get_historical_weather(days_ago=days_ago)
    return sum([day['day']['totalprecip_in'] for day in data['forecast']['forecastday']])

def get_forecasted_precipitation_from_rain_in_inches(self, days=3, decay_factor=0.5):
    """
    Get forecasted rain amount.

    Weigh future values lower.

    TODO could improve by using forecast confidence, if available.
    """
    data = get_forecasted_weather(days=days)
    return sum([day['day']['totalprecip_in'] * (decay_factor ^ i) for i, day in enumerate(data['forecast']['forecastday'])])

def get_duration_in_seconds(self, actuator: Actuator) -> int:
    """
    Calculate the total time the sprinkler needs to run to get the desired amount
    of amount of water.

    This takes the flow rate of the sprinkler into account and then uses other
    information (such as weather) to modify the time.
    """
    required_inches_of_water_per_week = actuator.base_inches_per_week
    rain_amount = get_precipitation_from_rain_in_inches(days_ago=6)
    forecasted_rain_amount = get_precipitation_from_rain_in_inches(days=2)

    recent_water_amount = actuator.get_recent_water_amount(days_ago=6)

    number_of_scheduled_days = actuator.scheduled_day_count
    baseline_duration = actuator.duration_in_minutes_per_scheduled_day
    rolling_weekly_shortfall = (required_inches_of_water_per_week - (rain_amount + sprinkler_amount))

    calculated_duration_in_seconds = (rolling_weekly_shortfall / self.flow_rate_per_minute) * 60

    if calculated_duration_in_seconds < SKIP_WATERING_THRESHOLD_IN_SECONDS:
        return 0

    # never water less than the minimum duration or more than the baseline duration
    duration_in_seconds = min(max(calculated_duration_in_seconds, MINIMUM_DURATION_IN_SECONDS), baseline_duration)

    return duration_in_seconds

def _run(actuator: Actuator):
    duration_in_seconds = get_duration_in_seconds(actuator)
    if duration_in_seconds:
        actuator.start(schedule_time=self)
        time.sleep(get_duration_in_seconds(actuator))
        actuator.stop(schedule_time=self)
    else:
        print('Skipping run')

def run():
    if self.should_run(self.actuator):
        self_run(self.actuator)

def should_run(actuator: Actuator):
    now = datetime.now()
    current_weekday = now.weekday()
    current_time = now.time()
    if self.weekday != current_weekday:
        return False

    if current_time > self.start_time:
        # is there already a run for the scheduled time today?
        already_triggered = ActuatorRun.objects.filter(schedule_time=self, start_datetime__date=now.date()).exists()

        if not already_triggered:
            return True

    return False
