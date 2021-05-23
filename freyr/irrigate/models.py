from datetime import datetime
from typing import Optional

from django.db import models, transaction
from django.db.models import Q
from irrigate.gpio import GPIO


class Device(models.Model):
    name = models.CharField(max_length=255, help_text='Unique ID for a given device (e.g. garage pi, garden pi)')

    def __str__(self):
        return self.name

# Create your models here.
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
        return self.name

    @property
    def gpio(self):
        return GPIO(self.gpio_pin)

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
        return self.total_duration_in_minutes_per_week / self.scheduled_day_count

    @property
    def scheduled_day_count(self):
        """
        """
        return self.schedule_days.all().count()


    @transaction.atomic
    def start(self, schedule_time: Optional['ScheduleTime'] = None):
        """
        Start the actuator
        """
        self.gpio.start()
        if not self.gpio.test_mode:
            ActuatorRun.objects.create(actuator=self, start_datetime=datetime.now(), schedule_time=schedule_time)

    @transaction.atomic
    def stop(self, schedule_time: Optional['ScheduleTime'] = None):
        """
        Stop the actuator
        """
        self.gpio.stop()
        if not self.gpio.test_mode:
            current_run = ActuatorRun.objects.get(actuator=self, end_datetime__isnull=True, schedule_time=schedule_time)
            current_run.end_datetime = datetime.now()
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

    def should_run(self, actuator: Actuator):
        # TODO move to separate scheduler module
        now = datetime.now()
        current_weekday = now.weekday()
        current_time = now.time()
        if self.weekday != current_weekday:
            return False

        if current_time > self.start_time:
            # is there already a run for the scheduled time today?
            not_already_triggered = ActuatorRun.objects.filter(schedule_time=self, start_datetime__date=now.date()).exists()

            if not already_triggered:
                return True

        return False

    def _run(self, actuator: Actuator):
        actuator.start(schedule_time=self)
        time.sleep(self.duration_in_minutes * 60)
        actuator.stop(schedule_time=self)


    def run(self):
        if self.should_run(self.actuator):
            self._run(self.actuator)

class ActuatorRunLog(models.Model):
    RUNNING = 'running'
    FINISHED = 'finished'

    actuator = models.ForeignKey(Actuator, on_delete=models.CASCADE)
    schedule_time = models.ForeignKey(ScheduleTime, blank=True, null=True, on_delete=models.CASCADE, help_text="Optional field indicating whether this is attached to a scheduled run. Will be blank if triggered manually")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    def __str__(self):
        return f'{self.start_datetime} - {self.end_datetime}'

    def status(self):
        if not self.end_datetime:
            return self.RUNNING
        return self.FINISHED
