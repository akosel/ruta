from django import forms

from irrigate.models import Actuator, ActuatorRunLog


MAX_ONE_OFF_DURATION_IN_MINUTES = 120


class OneOffRunForm(forms.Form):
    actuator = forms.ModelChoiceField(
        queryset=Actuator.objects.order_by("name"),
        empty_label="Select a zone",
    )
    duration_in_minutes = forms.IntegerField(
        min_value=1,
        max_value=MAX_ONE_OFF_DURATION_IN_MINUTES,
        widget=forms.NumberInput(
            attrs={"min": 1, "max": MAX_ONE_OFF_DURATION_IN_MINUTES}
        ),
    )

    def clean_actuator(self):
        actuator = self.cleaned_data["actuator"]
        is_running = ActuatorRunLog.objects.filter(
            actuator=actuator,
            end_datetime__isnull=True,
        ).exists()
        if is_running:
            raise forms.ValidationError("This zone is already running.")
        return actuator
