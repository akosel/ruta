# Generated by Django 3.2.4 on 2022-11-06 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("irrigate", "0012_scheduletime_duration_in_minutes"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduletime",
            name="enabled",
            field=models.BooleanField(default=True),
        ),
    ]
