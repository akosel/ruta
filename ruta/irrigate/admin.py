from django.contrib import admin, messages

from irrigate.models import Actuator, ActuatorRunLog, Device, ScheduleTime


@admin.action(description="Start actuator")
def start(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, "Only able to turn on 1 at a time")
        return
    queryset[0].start()


@admin.action(description="Stop actuator")
def stop(modeladmin, request, queryset):
    for actuator in queryset:
        actuator.stop()


class ActuatorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "gpio_pin",
        "calculated_duration_in_minutes",
        "next_run_duration_in_minutes",
        "temperature_multiplier",
        "todays_high_temperature",
        "next_1_days_precipitation",
        "last_1_days_precipitation",
        "last_3_days_precipitation",
        "next_3_days_precipitation",
        "last_7_days_precipitation",
    ]

    actions = [start, stop]

    def next_3_days_precipitation(self, actuator):
        days = 3
        from_rain = actuator.get_forecasted_precipitation_from_rain_in_inches(days=days)
        return f"{from_rain:.2f}"

    def next_1_days_precipitation(self, actuator):
        days = 1
        from_rain = actuator.get_forecasted_precipitation_from_rain_in_inches(days=days)
        return f"{from_rain:.2f}"

    def last_1_days_precipitation(self, actuator):
        days_ago = 1
        from_rain = actuator.get_precipitation_from_rain_in_inches(days_ago=days_ago)
        from_sprinklers = actuator.get_recent_water_amount_in_inches(days_ago=days_ago)
        return f"Rain: {from_rain:.2f} -- Sprinklers: {from_sprinklers:.2f}"

    def last_3_days_precipitation(self, actuator):
        days_ago = 3
        from_rain = actuator.get_precipitation_from_rain_in_inches(days_ago=days_ago)
        from_sprinklers = actuator.get_recent_water_amount_in_inches(days_ago=days_ago)
        return f"Rain: {from_rain:.2f} -- Sprinklers: {from_sprinklers:.2f}"

    def last_7_days_precipitation(self, actuator):
        days_ago = 7
        from_rain = actuator.get_precipitation_from_rain_in_inches(days_ago=days_ago)
        from_sprinklers = actuator.get_recent_water_amount_in_inches(days_ago=days_ago)
        return f"Rain: {from_rain:.2f} -- Sprinklers: {from_sprinklers:.2f}"

    def calculated_duration_in_minutes(self, actuator):
        return round(actuator._get_base_duration_in_seconds() / 60, 2)

    def next_run_duration_in_minutes(self, actuator):
        return round(actuator.get_duration_in_seconds() / 60, 2)

    def todays_high_temperature(self, actuator):
        return actuator.get_todays_high_temperature()

    def temperature_multiplier(self, actuator):
        return actuator.get_temperature_watering_adjustment_multiplier()


admin.site.register(Actuator, ActuatorAdmin)
admin.site.register(ActuatorRunLog)
admin.site.register(Device)
admin.site.register(ScheduleTime)
