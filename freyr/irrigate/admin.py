from django.contrib import admin

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime

@admin.action(description='Start actuator')
def start(modeladmin, request, queryset):
    if queryset.count() > 1:
        raise ValueError('Only able to turn on 1 at a time')
    queryset[0].start()

@admin.action(description='Stop actuator')
def stop(modeladmin, request, queryset):
    if queryset.count() > 1:
        raise ValueError('Only able to turn on 1 at a time')
    queryset[0].stop()

class ActuatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'gpio_pin']
    actions = [start, stop]

admin.site.register(Actuator, ActuatorAdmin)
admin.site.register(ActuatorRunLog)
admin.site.register(Device)
admin.site.register(ScheduleTime)
