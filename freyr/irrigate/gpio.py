import inspect
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class GPIO:
    def __init__(self, pin: int):
        self.test_mode = settings.TEST
        self.gpio = None
        try:
            import lgpio
            self.gpio = lgpio
        except:
            logger.info('Unable to import lgpio...running in test mode.')
            self.test_mode = True

        self.pin = pin
        if not self.test_mode:
            self.handle = self.gpio.gpiochip_open(0)
            self.setup()

    def setup(self):
        self.gpio.gpio_claim_output(self.handle, self.pin)

    def start(self):
        self.gpio.gpio_write(self.handle, self.pin, 1)

    def stop(self):
        self.gpio.gpio_write(self.handle, self.pin, 0)

    def close(self):
        self.stop()
        self.gpio.gpiochip_close(self.handle)


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
