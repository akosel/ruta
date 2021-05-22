from django.contrib import admin

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleDay, ScheduleTime

admin.site.register(Actuator)
admin.site.register(ActuatorRunLog)
admin.site.register(Device)
admin.site.register(ScheduleDay)
admin.site.register(ScheduleTime)
