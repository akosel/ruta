from django.contrib import admin

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime

admin.site.register(Actuator)
admin.site.register(ActuatorRunLog)
admin.site.register(Device)
admin.site.register(ScheduleTime)
