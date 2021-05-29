from django.core.management.base import BaseCommand, CommandError
from irrigate.schedule import run_all


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        run_all()
