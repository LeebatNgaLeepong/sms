"""
Recompute letter and grade_points for existing grades on the University of
Antique 1.00-5.00 scale. Rows written before the scale change still carry the
old A-F letters and 0.00-4.00 points, which made the dashboard distribution and
passing rate report wrong values.
"""

from django.db import migrations


def recompute_grades(apps, schema_editor):
    from grades.models import compute_grade_details

    Grade = apps.get_model('grades', 'Grade')
    for grade in Grade.objects.all().iterator():
        letter, points = compute_grade_details(grade.score)
        if grade.letter != letter or grade.grade_points != points:
            grade.letter = letter
            grade.grade_points = points
            # Bypass Grade.save(), which does not exist on historical models.
            Grade.objects.filter(pk=grade.pk).update(letter=letter, grade_points=points)


def noop(apps, schema_editor):
    """Reversing restores nothing meaningful; the values are recomputed on save."""


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0002_alter_grade_grade_points_alter_grade_letter'),
    ]

    operations = [
        migrations.RunPython(recompute_grades, noop),
    ]
