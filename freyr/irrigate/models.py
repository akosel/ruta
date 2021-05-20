from django.db import models


# Create your models here.
class Actuator(models.Model):
    """
    An actuator is a component of a machine that is responsible for moving and
    controlling a mechanism or system, for example by opening a valve.

    In our case, this represents a sprinkler zone.
    """
    name = models.CharField(max_length=255)
    gpio_pin = models.SmallIntegerField()

    def start(self):
        """
        Start the actuator
        """
        pass

    def stop(self):
        """
        Stop the actuator
        """
        pass
