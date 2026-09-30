"""
Only one time slot may start at a given time on a given day.

Previously uniqueness included end_time, so a day could have several slots
starting at the same hour with different lengths. A timetable cell is keyed by
day and start time, so those duplicates were redundant and made the grid
ambiguous.

Before adding the constraint, orphan duplicates (slots with no scheduled
classes) are removed. If duplicates that are actually in use remain, the
migration stops and asks for them to be resolved rather than silently moving or
dropping real classes.
"""

from django.db import migrations, models


def drop_orphan_duplicate_slots(apps, schema_editor):
    TimeSlot = apps.get_model('schedules', 'TimeSlot')

    seen = set()
    blockers = []
    StudentSchedule = apps.get_model('schedules', 'StudentSchedule')

    for slot in TimeSlot.objects.order_by('day', 'start_time', 'id'):
        key = (slot.day, slot.start_time)
        if key not in seen:
            seen.add(key)
            continue
        if StudentSchedule.objects.filter(time_slot=slot).exists():
            blockers.append(f'{slot.day} {slot.start_time} (slot id={slot.id})')
        else:
            slot.delete()

    if blockers:
        raise RuntimeError(
            'Cannot enforce one time slot per day and start time. These duplicate '
            'start times are in use and must be merged by hand first: '
            + ', '.join(blockers)
        )


def noop(apps, schema_editor):
    """No safe reverse: the stricter constraint is dropped, data is untouched."""


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0003_timeslot_end_time'),
    ]

    operations = [
        migrations.RunPython(drop_orphan_duplicate_slots, noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AddConstraint(
                    model_name='timeslot',
                    constraint=models.UniqueConstraint(
                        fields=['day', 'start_time'],
                        name='unique_timeslot_day_start',
                    ),
                ),
            ],
            state_operations=[
                # SQLite cannot drop a composite unique_together cleanly. The
                # leftover index is redundant under the stricter new constraint
                # but is kept rather than rebuilt, so only state is updated here.
                migrations.AlterUniqueTogether(
                    name='timeslot',
                    unique_together=set(),
                ),
                migrations.AddConstraint(
                    model_name='timeslot',
                    constraint=models.UniqueConstraint(
                        fields=['day', 'start_time'],
                        name='unique_timeslot_day_start',
                    ),
                ),
            ],
        ),
    ]
