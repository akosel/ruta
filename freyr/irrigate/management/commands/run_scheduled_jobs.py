import logging

from django.core.management.base import BaseCommand, CommandError
from irrigate.monitor import MonitoringEvent, MonitoringEventStatus, emit
from irrigate.schedule import run_all

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, dry_run=False, *args, **kwargs):
        logger.info(f'Checking for runnable jobs. dry_run: {dry_run}')
        try:
            actuators_that_ran = run_all(dry_run=dry_run)
        except Exception as e:
            event = MonitoringEvent(name=f'Error while running scheduled jobs {e}', status=MonitoringEventStatus.FAILURE)
            emit(event)
            return
        if actuators_that_ran:
            event = MonitoringEvent(name=f'Success ran for {actuators_that_ran}', status=MonitoringEventStatus.SUCCESS)
            emit(event)

        logger.info(f'Finished checking for runnable jobs. dry_run: {dry_run}')
