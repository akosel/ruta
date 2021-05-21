from django.contrib import admin

from irrigate.models import Actuator, ActuatorCollection, ActuatorRun, ScheduleTime

admin.site.register(Actuator)
admin.site.register(ActuatorCollection)
admin.site.register(ActuatorRun)
admin.site.register(ScheduleTime)
