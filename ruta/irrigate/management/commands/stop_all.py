import logging

from django.core.management.base import BaseCommand, CommandError
from irrigate.schedule import stop_all

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info(f'Stopping all actuators')
        stop_all()
        logger.info(f'Stopped all actuators')
