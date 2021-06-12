import logging
from datetime import timedelta
from typing import Optional

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from irrigate.constants import (MINIMUM_WATER_DURATION_IN_SECONDS,
                                SKIP_WATERING_THRESHOLD_IN_SECONDS)
from irrigate.gpio import GPIO
from irrigate.weather import get_current_weather, get_forecasted_weather, get_historical_weather

logger = logging.getLogger(__name__)

class Device(models.Model):
    name = models.CharField(max_length=255, help_text='Unique ID for a given device (e.g. garage pi, garden pi)')

    def __str__(self):
        return self.name

class Actuator(models.Model):
    """
    An actuator is a component of a machine that is responsible for moving and
    controlling a mechanism or system, for example by opening a valve.

    In our case, this represents a sprinkler zone.
    """
    name = models.CharField(max_length=255, help_text='A name to help identify which actuator this is')
    gpio_pin = models.SmallIntegerField(help_text='GPIO pin on the raspberry pi')
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    flow_rate_per_minute = models.FloatField(default=0.025)
    base_inches_per_week = models.FloatField(default=1)

    def __str__(self):
        return f'{self.name} - {self.gpio_pin}'

    def get_precipitation_from_rain_in_inches(self, days_ago=3):
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

    def get_todays_high_temperature(self):
        forecasted_weather = get_forecasted_weather(days=1)
        return forecasted_weather['forecast']['forecastday'][0]['day']['maxtemp_f']

    def get_temperature_watering_adjustment_multiplier(self) -> float:
        max_temperature = self.get_todays_high_temperature()

        if max_temperature >=85:
            return 1.3
        elif max_temperature >= 65:
            return 1
        elif max_temperature >= 45:
            return .7

        return 0

    def _get_base_duration_in_seconds(self):
        required_inches_of_water_per_week = self.base_inches_per_week

        baseline_duration = self.duration_in_minutes_per_scheduled_day * 60
        rain_amount = self.get_precipitation_from_rain_in_inches(days_ago=3)
        sprinkler_amount = self.get_recent_water_amount_in_inches(days_ago=3)

        rolling_weekly_shortfall = (required_inches_of_water_per_week - (rain_amount + sprinkler_amount))
        logger.info(f'Rain amount: {rain_amount} - Sprinkler amount: {sprinkler_amount} - Baseline duration - {baseline_duration} - Shortfall: {rolling_weekly_shortfall}')

        return (rolling_weekly_shortfall / self.flow_rate_per_minute) * 60

    def get_duration_in_seconds(self) -> int:
        """
        Calculate the total time the sprinkler needs to run to get the desired amount
        of amount of water.

        This takes the flow rate of the sprinkler into account and then uses other
        information (such as weather) to modify the time.

        There are controls in place to ensure the watering time stays within sane
        boundaries.
        """

        base_duration_in_seconds = self._get_base_duration_in_seconds()
        temperature_multiplier = self.get_temperature_watering_adjustment_multiplier()
        logger.info(f'Base duration is {base_duration_in_seconds} and temperature multipler is {temperature_multiplier}')

        calculated_duration_in_seconds = base_duration_in_seconds * temperature_multiplier

        if calculated_duration_in_seconds < SKIP_WATERING_THRESHOLD_IN_SECONDS:
            return 0

        # never water less than the minimum duration or more than the baseline duration
        baseline_duration = self.duration_in_minutes_per_scheduled_day * 60
        duration_in_seconds = min(max(calculated_duration_in_seconds, MINIMUM_WATER_DURATION_IN_SECONDS), baseline_duration)


        return duration_in_seconds

    @property
    def total_duration_in_minutes_per_week(self):
        """
        Total minutes of watering needed per week
        """
        if not self.flow_rate_per_minute:
            return 0
        return self.base_inches_per_week / self.flow_rate_per_minute

    @property
    def duration_in_minutes_per_scheduled_day(self):
        """
        Number of minutes to run per day
        """
        count = self.get_number_of_scheduled_times()
        if count:
            return self.total_duration_in_minutes_per_week / count
        return 0

    def get_number_of_scheduled_times(self):
        """
        Get the number of times the actuator is scheduled to run
        """
        return self.scheduletime_set.all().count()

    def get_recent_water_amount_in_inches(self, days_ago=7):
        now = timezone.now()
        start_datetime = now - timedelta(days=days_ago)
        recent_runs = ActuatorRunLog.objects.filter(actuator=self, start_datetime__gt=start_datetime)

        total_minutes = 0
        for run in recent_runs:
            # being defensive here. if no end datetime is specified, do not
            # count it
            if not run.end_datetime:
                continue
            total_minutes += (run.end_datetime - run.start_datetime).seconds / 60

        return total_minutes * self.flow_rate_per_minute


    @transaction.atomic
    def start(self, schedule_time: Optional['ScheduleTime'] = None):
        """
        Start the actuator
        """
        with GPIO(self.gpio_pin) as gpio:
            gpio.start()
            if schedule_time:
                ActuatorRunLog.objects.create(actuator=self, start_datetime=timezone.now(), schedule_time=schedule_time)

    @transaction.atomic
    def stop(self, schedule_time: Optional['ScheduleTime'] = None, duration_in_seconds: Optional[int] = None):
        """
        Stop the actuator
        """
        with GPIO(self.gpio_pin) as gpio:
            gpio.stop()
            if schedule_time:
                try:
                    current_run = ActuatorRunLog.objects.get(actuator=self, end_datetime__isnull=True, schedule_time=schedule_time)
                except ActuatorRunLog.DoesNotExist:
                    logger.warn(f'Unable to find matching run log for {self} at scheduled time {schedule_time}')
                    return

                end_datetime = timezone.now() if not duration_in_seconds else (current_run.start_datetime + timedelta(seconds=duration_in_seconds))
                current_run.end_datetime = end_datetime
                current_run.save()

class ScheduleTime(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0
        TUESDAY = 1
        WEDNESDAY = 2
        THURSDAY = 3
        FRIDAY = 4
        SATURDAY = 5
        SUNDAY = 6

    start_time = models.TimeField()
    weekday = models.IntegerField(choices=Weekday.choices)
    actuators = models.ManyToManyField(Actuator)

    def __str__(self):
        return f'{self.Weekday(self.weekday).name} - {self.start_time} - {list(self.actuators.all())}'

class ActuatorRunLog(models.Model):
    RUNNING = 'running'
    FINISHED = 'finished'

    actuator = models.ForeignKey(Actuator, on_delete=models.CASCADE)
    schedule_time = models.ForeignKey(ScheduleTime, blank=True, null=True, on_delete=models.CASCADE, help_text="Optional field indicating whether this is attached to a scheduled run. Will be blank if triggered manually")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.start_datetime} - {self.end_datetime} - {self.status} - {self.actuator}'

    @property
    def status(self):
        if not self.end_datetime:
            return self.RUNNING
        return self.FINISHED

