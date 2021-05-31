import inspect
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class GPIO:
    def __init__(self, pin: int):
        self.test_mode = settings.TEST
        self.gpio = None
        try:
            import RPi.GPIO as gpio
            self.gpio = gpio
        except:
            self.test_mode = True

        self.pin = pin

    def setup(self):
        gpio.setmode(self.gpio.BCM)
        gpio.setup(self.pin, self.gpio.OUT)

    def start(self):
        gpio.output(self.pin, self.gpio.HIGH)

    def stop(self):
        gpio.output(self.pin, self.gpio.LOW)


def decorator(func):
    def wrapper(self, *args, **kwargs):
        in_test_mode = getattr(self, 'test_mode', False)
        if in_test_mode:
            logger.info(f'Would call {func.__name__}')
            return
        return func(self, *args, **kwargs)
    return wrapper

for name, fn in inspect.getmembers(GPIO, inspect.isfunction):
    setattr(GPIO, name, decorator(fn))
