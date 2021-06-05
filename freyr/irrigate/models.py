import logging
from datetime import timedelta
from typing import Optional

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from irrigate.gpio import GPIO

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

    @property
    def gpio(self):
        if not getattr(self, '_gpio', None):
            self._gpio = GPIO(self.gpio_pin)

        return self._gpio

    @property
    def total_duration_in_minutes_per_week(self):
        """
        Total minutes of watering needed per week
        """
        return self.base_inches_per_week / self.flow_rate_per_minute

    @property
    def duration_in_minutes_per_scheduled_day(self):
        """
        Number of minutes to run per day
        """
        return self.total_duration_in_minutes_per_week / self.get_number_of_scheduled_times()

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
        self.gpio.start()
        ActuatorRunLog.objects.create(actuator=self, start_datetime=timezone.now(), schedule_time=schedule_time)

    @transaction.atomic
    def stop(self, schedule_time: Optional['ScheduleTime'] = None, duration_in_seconds: Optional[int] = None):
        """
        Stop the actuator
        """
        self.gpio.stop()
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
    SCHEDULED_RUN_END_BUFFER = 5

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
        return f'{self.start_datetime} - {self.end_datetime} - {self.status}'

    @property
    def status(self):
        if not self.end_datetime:
            return self.RUNNING
        return self.FINISHED

