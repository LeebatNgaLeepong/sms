"""
Remove schedule rows whose term values are not valid options.

Term values were free text, so unvalidated input wrote rows such as
school_year="{'a': 1}" and semester="['x']", and the earlier default of
"1st Sem 2026" doubled the year into the semester field. Those rows produced
duplicate-looking timetables, so they are dropped here; valid rows are left
untouched and can be rebuilt with Auto-Generate.
"""

from django.conf import settings
from django.db import migrations


def purge_invalid_term_rows(apps, schema_editor):
    StudentSchedule = apps.get_model('schedules', 'StudentSchedule')

    invalid = StudentSchedule.objects.exclude(
        semester__in=settings.SEMESTER_CHOICES
    ).exclude(semester='')
    invalid |= StudentSchedule.objects.exclude(
        school_year__in=settings.SCHOOL_YEAR_CHOICES
    ).exclude(school_year='')
    count = invalid.count()
    invalid.delete()
    if count:
        print(f'  removed {count} schedule row(s) with an invalid term')


def noop(apps, schema_editor):
    """Nothing to restore: the removed rows had unusable term values."""


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0005_alter_studentschedule_semester_section_and_more'),
    ]

    operations = [
        migrations.RunPython(purge_invalid_term_rows, noop),
    ]
