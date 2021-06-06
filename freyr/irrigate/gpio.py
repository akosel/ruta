import inspect
import logging
from unittest.mock import Mock

from django.conf import settings

logger = logging.getLogger(__name__)

class GPIO:
    def __init__(self, pin: int):
        try:
            import lgpio
            self._gpio = lgpio
        except:
            logger.warn('Unable to import lgpio...running in test mode.')
            self._gpio = Mock()

        if settings.TEST:
            self._gpio = Mock()

        self.pin = pin
        self.handle = self._gpio.gpiochip_open(0)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def setup(self):
        self._gpio.gpio_claim_output(self.handle, self.pin)

    def start(self):
        self._gpio.gpio_write(self.handle, self.pin, 0)

    def stop(self):
        self._gpio.gpio_write(self.handle, self.pin, 1)

    def read(self):
        return self._gpio.gpio_read(self.handle, self.pin)

    def close(self):
        self._gpio.gpiochip_close(self.handle)
