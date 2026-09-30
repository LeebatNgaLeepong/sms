"""
Initial migration for schedules app.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('students', '0002_student_enrolled_subjects'),
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday')], max_length=3, help_text='Day of the week.')),
                ('start_time', models.TimeField(help_text='Start time of the slot (e.g., 07:00).')),
                ('duration_hours', models.PositiveSmallIntegerField(default=2, help_text='Duration of the slot in hours (e.g., 2 for 2 hours).')),
                ('slot_type', models.CharField(choices=[('lec', 'Lecture'), ('lab', 'Laboratory')], default='lec', max_length=3, help_text='Type of class: Lecture or Laboratory.')),
                ('label', models.CharField(blank=True, help_text="Optional label (e.g., 'Period 1').", max_length=50)),
            ],
            options={
                'ordering': ['day', 'start_time'],
                'unique_together': {('day', 'start_time', 'duration_hours')},
            },
        ),
        migrations.CreateModel(
            name='StudentSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.CharField(blank=True, help_text="Semester (e.g., '1st Sem 2026').", max_length=50)),
                ('school_year', models.CharField(blank=True, help_text='School year (e.g., \'2025-2026\').', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(help_text='The student this schedule belongs to.', on_delete=models.deletion.CASCADE, related_name='schedules', to='students.student')),
                ('subject', models.ForeignKey(help_text='The subject scheduled.', on_delete=models.deletion.CASCADE, related_name='schedules', to='subjects.subject')),
                ('time_slot', models.ForeignKey(help_text='The time slot for this subject.', on_delete=models.deletion.CASCADE, related_name='student_schedules', to='schedules.timeslot')),
            ],
            options={
                'ordering': ['student__id', 'time_slot__day', 'time_slot__start_time'],
                'unique_together': {('student', 'subject', 'semester', 'school_year')},
            },
        ),
    ]