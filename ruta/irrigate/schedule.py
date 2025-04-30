import logging
import time
from typing import List, Optional
from datetime import timedelta

from django.utils import timezone

from irrigate.monitor import MonitoringEvent, MonitoringEventStatus, emit
from irrigate.models import Actuator, ActuatorRunLog, ScheduleTime

logger = logging.getLogger(__name__)

# Constants for grass seed mode
GRASS_SEED_DURATION_SECONDS = 60  # 1 minute
GRASS_SEED_INTERVAL_HOURS = 5     # Every 5 hours


def _run(
    actuator: Actuator,
    schedule_time: Optional[ScheduleTime] = None,
    dry_run: bool = False,
    duration_override: Optional[int] = None,
) -> int:
    if duration_override:
        duration_in_seconds = duration_override
    elif schedule_time and schedule_time.duration_in_minutes:
        duration_in_seconds = schedule_time.duration_in_minutes * 60
    else:
        duration_in_seconds = actuator.get_duration_in_seconds()
    if not dry_run:
        actuator.start(schedule_time=schedule_time)
        time.sleep(duration_in_seconds)
        actuator.stop(schedule_time=schedule_time)
    else:
        logger.info(f"Would run {actuator} for {duration_in_seconds} second(s)")
    return duration_in_seconds


def has_run(schedule_time: ScheduleTime, actuator: Actuator):
    runs = ActuatorRunLog.objects.filter(
        schedule_time=schedule_time,
        actuator=actuator,
    )

    # for one-offs, we only run them once ever, but for recurring we run them
    # once per week
    if schedule_time.run_type == ScheduleTime.RunType.RECURRING:
        now = timezone.now().date()
        runs = runs.filter(start_datetime__date=now)

    return runs.exists()


def has_grass_seed_run_recently(actuator: Actuator):
    """
    Check if an actuator has run in grass seed mode within the current hour window
    """
    now = timezone.now()
    start_of_current_window = now.replace(minute=0, second=0, microsecond=0)
    
    # Check for any runs within the current hour window
    recent_runs = ActuatorRunLog.objects.filter(
        actuator=actuator,
        start_datetime__gte=start_of_current_window,
        end_datetime__isnull=False
    )
    
    # If we have any recent runs that lasted about 1 minute, consider it a grass seed run
    for run in recent_runs:
        duration_seconds = (run.end_datetime - run.start_datetime).total_seconds()
        if abs(duration_seconds - GRASS_SEED_DURATION_SECONDS) < 5:  # Allow for small timing variations
            return True
    
    return False


def run_all(dry_run: bool = False) -> List[Actuator]:
    """
    Run sprinklers scheduled to run in order, one at a time.
    Also handles grass seed mode for applicable actuators.

    Returns sprinklers that ran, if any.
    """
    now = timezone.now()
    weekday = now.weekday()
    hour = now.time()
    
    # Regular scheduled runs
    schedule_times = ScheduleTime.objects.filter(
        enabled=True,
        weekday=weekday,
        start_time__lte=hour,
    )
    verb = "running" if not dry_run else "simulating"
    logger.info(f"Scheduled times: {schedule_times}")
    actuators_that_ran = []
    
    # First run the regularly scheduled actuators
    for schedule_time in schedule_times:
        for actuator in schedule_time.actuators.all():
            if has_run(schedule_time, actuator):
                logger.info(
                    f"Actuator {actuator} has already run today for {schedule_time}"
                )
                continue
            event = MonitoringEvent(
                name=f"Starting run for {actuator} - dry_run: {dry_run}",
                status=MonitoringEventStatus.IN_PROGRESS,
            )
            emit(event)

            if not dry_run:
                logger.info(f"{verb} actuator {actuator}")
                seconds_run = _run(actuator, schedule_time=schedule_time)
                minutes_run = seconds_run / 60
                event = MonitoringEvent(
                    name=f"Ran {actuator} for {minutes_run}",
                    status=MonitoringEventStatus.IN_PROGRESS,
                )
                if seconds_run:
                    logger.info(
                        f"Finished {verb} actuator {actuator} for {seconds_run} second(s)"
                    )
                else:
                    logger.info(f"Skipped {verb} actuator {actuator}")
            actuators_that_ran.append(actuator)

    # Now handle grass seed mode actuators - they run every 5 hours for 1 minute
    current_hour = now.hour
    if current_hour % GRASS_SEED_INTERVAL_HOURS == 0:  # Run at hours 0, 5, 10, 15, 20
        grass_seed_actuators = Actuator.objects.filter(grass_seed_mode=True)
        logger.info(f"Found {grass_seed_actuators.count()} actuators in grass seed mode")
        
        for actuator in grass_seed_actuators:
            # Check if it has already run during this hour window
            if has_grass_seed_run_recently(actuator):
                logger.info(f"Actuator {actuator} has already run in grass seed mode this hour")
                continue
                
            # Create a temporary schedule time for logging purposes
            schedule_time = ScheduleTime.objects.create(
                run_type=ScheduleTime.RunType.ONE_OFF,
                start_time=now.time(),
                weekday=weekday,
                duration_in_minutes=GRASS_SEED_DURATION_SECONDS / 60,
            )
            schedule_time.actuators.add(actuator)
            
            event = MonitoringEvent(
                name=f"Starting grass seed mode run for {actuator} - dry_run: {dry_run}",
                status=MonitoringEventStatus.IN_PROGRESS,
            )
            emit(event)
            
            if not dry_run:
                logger.info(f"{verb} actuator {actuator} in grass seed mode")
                seconds_run = _run(
                    actuator, 
                    schedule_time=schedule_time,
                    duration_override=GRASS_SEED_DURATION_SECONDS
                )
                event = MonitoringEvent(
                    name=f"Ran {actuator} in grass seed mode",
                    status=MonitoringEventStatus.SUCCESS,
                )
                emit(event)
                logger.info(f"Finished {verb} actuator {actuator} in grass seed mode")
            actuators_that_ran.append(actuator)
    
    return actuators_that_ran


def stop_all():
    """
    This will run off all sprinklers
    """
    actuators = Actuator.objects.all()
    for actuator in actuators:
        logger.info(f"Stopping {actuator} ")
        actuator.stop()
        logger.info(f"Stopped {actuator} ")
