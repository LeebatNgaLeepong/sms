"""
Replace the derived end time with a stored, editable one.

TimeSlot.end_time was a property computed from start_time + duration_hours, so
staff could not say when a class finished. Add a real end_time column, backfill
it from the existing durations, and make it required.
"""

from datetime import date, datetime, timedelta

from django.db import migrations, models


def backfill_end_time(apps, schema_editor):
    TimeSlot = apps.get_model('schedules', 'TimeSlot')
    for slot in TimeSlot.objects.filter(end_time__isnull=True).iterator():
        start_dt = datetime.combine(date.today(), slot.start_time)
        end_time = (start_dt + timedelta(hours=slot.duration_hours)).time()
        # Bypass the historical model's save() and any current validation.
        TimeSlot.objects.filter(pk=slot.pk).update(end_time=end_time)


def noop(apps, schema_editor):
    """No safe reverse: the original end time was derived, not stored."""


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0002_alter_studentschedule_options_alter_timeslot_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeslot',
            name='end_time',
            field=models.TimeField(blank=True, default=None, null=True),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_end_time, noop),
        migrations.AlterField(
            model_name='timeslot',
            name='end_time',
            field=models.TimeField(
                help_text='End time of the slot (e.g., 09:00). Must be after the start time.'
            ),
        ),
        migrations.AlterField(
            model_name='timeslot',
            name='duration_hours',
            field=models.PositiveSmallIntegerField(
                default=2,
                editable=False,
                help_text='Derived from start_time and end_time.',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='timeslot',
            unique_together={('day', 'start_time', 'end_time')},
        ),
    ]
