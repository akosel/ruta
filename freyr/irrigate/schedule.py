from irrigate.models import Actuator, ActuatorRun, ScheduleTime
from irrigate.weather import get_historical_weather




def should_run(self, actuator: Actuator):
    now = datetime.now()
    current_weekday = now.weekday()
    current_time = now.time()
    if self.weekday != current_weekday:
        return False

    if current_time > self.start_time:
        # is there already a run for the scheduled time today?
        already_triggered = ActuatorRun.objects.filter(schedule_time=self, start_datetime__date=now.date()).exists()

        if not already_triggered:
            return True

    return False

def get_precipitation_from_rain_in_inches(self, days_ago=7):
    data = get_historical_weather(days_ago=days_ago)
    return sum([day['day']['totalprecip_in'] for day in data['forecast']['forecastday']])

def get_duration(self, actuator: Actuator) -> int:
    base_duration = actuator.duration_in_minutes_per_scheduled_day

def _run(self, actuator: Actuator):
    actuator.start(schedule_time=self)
    time.sleep(get_duration(actuator))
    actuator.stop(schedule_time=self)


def run(self):
    if self.should_run(self.actuator):
        self._run(self.actuator)
