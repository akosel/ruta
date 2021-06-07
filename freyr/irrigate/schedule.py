import logging
import time
from typing import List, Optional

from django.utils import timezone

from irrigate.monitor import MonitoringEvent, MonitoringEventStatus, emit
from irrigate.models import Actuator, ActuatorRunLog, ScheduleTime

logger = logging.getLogger(__name__)


def _run(actuator: Actuator, schedule_time: Optional[ScheduleTime] = None, dry_run: bool = False) -> int:
    duration_in_seconds = actuator.get_duration_in_seconds()
    if duration_in_seconds:
        if not dry_run:
            actuator.start(schedule_time=schedule_time)
            time.sleep(duration_in_seconds)
            actuator.stop(schedule_time=schedule_time)
        else:
            logger.info(f'Would run {actuator} for {duration_in_seconds} second(s)')
    return duration_in_seconds

def has_run(schedule_time: ScheduleTime, actuator: Actuator):
    now = timezone.now().date()
    return ActuatorRunLog.objects.filter(schedule_time=schedule_time, actuator=actuator, start_datetime__date=now).exists()

def run_all(dry_run: bool = False) -> List[Actuator]:
    """
    Run sprinklers scheduled to run in order, one at a time.

    Returns sprinklers that ran, if any.
    """
    now = timezone.now()
    weekday = now.weekday()
    hour = now.time()
    schedule_times = ScheduleTime.objects.filter(weekday=weekday, start_time__lte=hour)
    verb = 'running' if not dry_run else 'simulating'
    logger.info(f'Scheduled times: {schedule_times}')
    actuators_that_ran = []
    for schedule_time in schedule_times:
        for actuator in schedule_time.actuators.all():
            if has_run(schedule_time, actuator):
                logger.info(f'Actuator {actuator} has already run today for {schedule_time}')
                continue
            event = MonitoringEvent(name=f'Starting run for {schedule_time}', status=MonitoringEventStatus.IN_PROGRESS)
            emit(event)

            if not dry_run:
                logger.info(f'{verb} actuator {actuator}')
                seconds_run = _run(actuator, schedule_time=schedule_time)
                if seconds_run:
                    logger.info(f'Finished {verb} actuator {actuator} for {seconds_run} second(s)')
                else:
                    logger.info(f'Skipped {verb} actuator {actuator}')
            actuators_that_ran.append(actuator)
    return actuators_that_ran

def stop_all():
    """
    This will run off all sprinklers
    """
    actuators = Actuator.objects.all()
    for actuator in actuators:
        logger.info(f'Stopping {actuator} ')
        actuator.stop()
        logger.info(f'Stopped {actuator} ')
