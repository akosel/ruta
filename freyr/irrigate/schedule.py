import logging
import time
from typing import List, Optional

from django.utils import timezone

from irrigate.constants import (MINIMUM_WATER_DURATION_IN_SECONDS,
                                SKIP_WATERING_THRESHOLD_IN_SECONDS)
from irrigate.models import Actuator, ActuatorRunLog, ScheduleTime
from irrigate.weather import get_current_weather, get_forecasted_weather, get_historical_weather

logger = logging.getLogger(__name__)

def get_precipitation_from_rain_in_inches(days_ago=7):
    """
    Get the amount of precipitation that has fallen.
    """
    data = get_historical_weather(days_ago=days_ago)
    return sum([day['day']['totalprecip_in'] for day in data['forecast']['forecastday']])

def get_forecasted_precipitation_from_rain_in_inches(days=3, decay_factor=0.5):
    """
    Get forecasted rain amount.

    Weigh future values lower.

    TODO could improve by using forecast confidence, if available.
    """
    data = get_forecasted_weather(days=days)
    return sum([day['day']['totalprecip_in'] * (decay_factor ^ i) for i, day in enumerate(data['forecast']['forecastday'])])

def get_temperature_watering_adjustment_multiplier() -> float:
    forecasted_weather = get_forecasted_weather(days=1)
    max_temperature = forecasted_weather['forecast']['forecastday'][0]['day']['maxtemp_f']

    if max_temperature >=85:
        return 1.3
    elif max_temperature >= 65:
        return 1
    elif max_temperature >= 45:
        return .7

    return 0

def get_duration_in_seconds(actuator: Actuator) -> int:
    """
    Calculate the total time the sprinkler needs to run to get the desired amount
    of amount of water.

    This takes the flow rate of the sprinkler into account and then uses other
    information (such as weather) to modify the time.
    """
    required_inches_of_water_per_week = actuator.base_inches_per_week

    rain_amount = get_precipitation_from_rain_in_inches(days_ago=3)
    sprinkler_amount = actuator.get_recent_water_amount_in_inches(days_ago=3)

    baseline_duration = actuator.duration_in_minutes_per_scheduled_day * 60
    rolling_weekly_shortfall = (required_inches_of_water_per_week - (rain_amount + sprinkler_amount))
    logger.info(f'Rain amount: {rain_amount} - Sprinkler amount: {sprinkler_amount} - Baseline duration - {baseline_duration} - Shortfall: {rolling_weekly_shortfall}')

    calculated_duration_in_seconds = (rolling_weekly_shortfall / actuator.flow_rate_per_minute) * 60

    logger.info(f'Calculated duration - {calculated_duration_in_seconds}')

    if calculated_duration_in_seconds < SKIP_WATERING_THRESHOLD_IN_SECONDS:
        return 0

    # never water less than the minimum duration or more than the baseline duration
    duration_in_seconds = min(max(calculated_duration_in_seconds, MINIMUM_WATER_DURATION_IN_SECONDS), baseline_duration)


    return duration_in_seconds

def _run(actuator: Actuator, schedule_time: Optional[ScheduleTime] = None, dry_run: bool = False) -> int:
    temperature_multiplier = get_temperature_watering_adjustment_multiplier()
    duration_in_seconds = get_duration_in_seconds(actuator) * temperature_multiplier
    logger.info(f'Base duration is {duration_in_seconds} and temperature multipler is {temperature_multiplier}')
    if duration_in_seconds:
        if not dry_run:
            actuator.start(schedule_time=schedule_time)
            time.sleep(duration_in_seconds)
            actuator.stop(schedule_time=schedule_time)
        else:
            logger.info(f'Would run {actuator} for {duration_in_seconds} second(s)')
    return duration_in_seconds

def has_run(schedule_time: ScheduleTime, actuator: Actuator):
    now = timezone.now().date()
    return ActuatorRunLog.objects.filter(schedule_time=schedule_time, actuator=actuator, start_datetime__date=now).exists()

def run_all(dry_run: bool = False) -> List[Actuator]:
    """
    Run sprinklers scheduled to run in order, one at a time.

    Returns sprinklers that ran, if any.
    """
    now = timezone.now()
    weekday = now.weekday()
    hour = now.time()
    schedule_times = ScheduleTime.objects.filter(weekday=weekday, start_time__lte=hour)
    verb = 'running' if not dry_run else 'simulating'
    logger.info(f'Scheduled times: {schedule_times}')
    actuators_that_ran = []
    for schedule_time in schedule_times:
        for actuator in schedule_time.actuators.all():
            if has_run(schedule_time, actuator):
                logger.info(f'Actuator {actuator} has already run today for {schedule_time}')
                continue

            if not dry_run:
                logger.info(f'{verb} actuator {actuator}')
                seconds_run = _run(actuator, schedule_time=schedule_time)
                if seconds_run:
                    logger.info(f'Finished {verb} actuator {actuator} for {seconds_run} second(s)')
                else:
                    logger.info(f'Skipped {verb} actuator {actuator}')
            actuators_that_ran.append(actuator)
    return actuators_that_ran

def stop_all():
    """
    This will run off all sprinklers
    """
    actuators = Actuator.objects.all()
    for actuator in actuators:
        logger.info(f'Stopping {actuator} ')
        actuator.stop()
        logger.info(f'Stopped {actuator} ')
