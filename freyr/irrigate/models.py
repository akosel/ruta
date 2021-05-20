from datetime import datetime

from django.db import models, transaction
from irrigate.gpio import GPIO


# Create your models here.
class Actuator(models.Model):
    """
    An actuator is a component of a machine that is responsible for moving and
    controlling a mechanism or system, for example by opening a valve.

    In our case, this represents a sprinkler zone.
    """
    name = models.CharField(max_length=255, help_text='A name to help identify which actuator this is')
    gpio_pin = models.SmallIntegerField(help='GPIO pin on the raspberry pi')
    device = models.CharField(max_length=255, help_text='Unique ID for a given device (e.g. garage pi, garden pi)'

    @property
    def gpio(self):
        return GPIO(self.gpio_pin)

    @transaction.atomic
    def start(self):
        """
        Start the actuator
        """
        self.gpio.start()
        if not self.gpio.test_mode:
            ActuatorRun.objects.create(actuator=self, start_time=datetime.now())

    @transaction.atomic
    def stop(self):
        """
        Stop the actuator
        """
        self.gpio.stop()
        if not self.gpio.test_mode:
            current_run = ActuatorRun.objects.get(actuator=self, end_time__isnull=True)
            current_run.end_time = datetime.now()
            current_run.save()

class ActuatorCollection(models.Model):
    name = models.CharField(max_length=255, help_text='A name to help identify which collection this is')
    actuators = models.ManyToManyField(Actuator, related_name='collections')

class ScheduleTime(models.Model):

    class Weekday(models.IntegerChoices):
        MONDAY = 0
        TUESDAY = 1
        WEDNESDAY = 2
        THURSDAY = 3
        FRIDAY = 4
        SATURDAY = 5
        SUNDAY = 6

    start_time = models.TimeField(required=True)
    day = models.IntegerField(max_length=1, choices=Weekday.choices, required=True)
    collection = models.ForeignKey(ActuatorCollection, on_delete=models.CASCADE)
    duration_in_minutes = models.PositiveIntegerField(required=True)

    def should_run(self, actuator: Actuator):
        # TODO move to separate scheduler module
        now = datetime.now()
        current_weekday = now.weekday()
        current_time = now.time()
        if self.day != current_weekday:
            return False

        if current_time > self.start_time:
            # TODO check if there is an existing run before returning

        return False

    def run(self):
        for actuator in self.collection.actuators.all():
            if self.should_run(actuator):
                actuator.start()
                time.sleep(self.duration_in_minutes * 60)

class ActuatorRun(models.Model):
    actuator = models.ForeignKey(Actuator, on_delete=models.CASCADE)
    start_time = models.DateTimeField(required=True)
    end_time = models.DateTimeField()

    def status(self):
        if not self.end_time:
            return 'running'
        return 'finished'
