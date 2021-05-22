from django.core.management.base import BaseCommand, CommandError
from irrigate.models import ScheduleDay


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for weekday in ScheduleDay.Weekday:
            for month in ScheduleDay.Month:
                ScheduleDay.objects.create(weekday=weekday.value, month=month.value)
