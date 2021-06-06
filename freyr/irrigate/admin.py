from django.contrib import admin, messages

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime

@admin.action(description='Start actuator')
def start(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, 'Only able to turn on 1 at a time')
        return
    queryset[0].start()

@admin.action(description='Stop actuator')
def stop(modeladmin, request, queryset):
    for actuator in queryset:
        actuator.stop()

class ActuatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'gpio_pin', 'get_duration_in_seconds', 'get_precipitation_from_rain_in_inches']
    actions = [start, stop]

admin.site.register(Actuator, ActuatorAdmin)
admin.site.register(ActuatorRunLog)
admin.site.register(Device)
admin.site.register(ScheduleTime)
