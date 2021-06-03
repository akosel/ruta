import logging

from django.core.management.base import BaseCommand, CommandError
from irrigate.schedule import run_all

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, dry_run=False, *args, **kwargs):
        logger.info(f'Checking for runnable jobs. dry_run: {dry_run}')
        run_all(dry_run=dry_run)
        logger.info(f'Finished checking for runnable jobs. dry_run: {dry_run}')
