# Generated by Django 3.2.4 on 2021-08-01 00:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('irrigate', '0010_alter_actuatorrunlog_end_datetime'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actuatorrunlog',
            options={'ordering': ('-start_datetime',)},
        ),
        migrations.AddField(
            model_name='scheduletime',
            name='run_type',
            field=models.IntegerField(choices=[(0, 'Recurring'), (1, 'One Off')], default=0),
        ),
    ]
