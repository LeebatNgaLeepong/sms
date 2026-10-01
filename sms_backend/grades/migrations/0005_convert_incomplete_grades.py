"""
Replace the 4.00 grade with INC.

4.00 was documented as "Incomplete" but was never produced by the score
conversion, and the dashboard treated it as a real band. It is now the INC
marker: no score, no grade points, and excluded from GPA and GWA because the
subject is not finished.
"""

from django.db import migrations


def convert_incomplete_grades(apps, schema_editor):
    Grade = apps.get_model('grades', 'Grade')

    converted = 0
    for grade in Grade.objects.filter(letter='4.00').iterator():
        Grade.objects.filter(pk=grade.pk).update(
            letter='INC',
            grade_points=None,
            score=None,
            is_incomplete=True,
        )
        converted += 1

    if converted:
        print(f'  converted {converted} grade(s) from 4.00 to INC')


def noop(apps, schema_editor):
    """A 4.00 grade is not a real value, so there is nothing to restore."""


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0004_grade_is_incomplete_alter_grade_grade_points_and_more'),
    ]

    operations = [
        migrations.RunPython(convert_incomplete_grades, noop),
    ]
