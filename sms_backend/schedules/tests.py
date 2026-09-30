"""
Tests for schedules app.
Validates automatic conflict-free schedule generation.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from schedules.models import StudentSchedule, TimeSlot
from schedules.scheduler import generate_schedule_for_subjects, regenerate_student_schedule, slots_overlap
from students.models import Student
from subjects.models import Subject

User = get_user_model()


class ScheduleGenerationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_s", email="admin_s@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.student_user = User.objects.create_user(
            username="stu_s", email="stu_s@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            name="Schedule Student",
            email="stu_s@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.subject1 = Subject.objects.create(code="CS101", name="Intro CS", units=3)
        self.subject2 = Subject.objects.create(code="CS201", name="Data Structures", units=4)
        self.subject3 = Subject.objects.create(code="MATH101", name="Calculus", units=4)

        # Create time slots
        from datetime import time
        TimeSlot.objects.create(day='Mon', start_time=time(7, 0), duration_hours=2, slot_type='lec')
        TimeSlot.objects.create(day='Mon', start_time=time(9, 0), duration_hours=2, slot_type='lec')
        TimeSlot.objects.create(day='Tue', start_time=time(7, 0), duration_hours=2, slot_type='lec')
        TimeSlot.objects.create(day='Tue', start_time=time(9, 0), duration_hours=2, slot_type='lec')
        TimeSlot.objects.create(day='Wed', start_time=time(7, 0), duration_hours=2, slot_type='lec')

    def test_generate_schedule_assigns_non_conflicting_slots(self):
        """Verify that auto-generated schedules do not have time conflicts."""
        results = generate_schedule_for_subjects(
            self.student,
            [self.subject1.id, self.subject2.id, self.subject3.id],
            semester='1st Sem',
            school_year='2025-2026',
        )

        # All subjects should be scheduled
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsNotNone(r['time_slot'], f"Subject {r['subject'].code} was not scheduled")

        # Verify no overlapping slots
        schedules = StudentSchedule.objects.filter(student=self.student)
        for i, s1 in enumerate(schedules):
            for s2 in schedules[i+1:]:
                self.assertFalse(
                    slots_overlap(s1.time_slot, s2.time_slot),
                    f"Conflict between {s1.subject.code} and {s2.subject.code}"
                )

    def test_generated_schedule_spreads_across_days(self):
        """Successive subjects should land on different days, not pile onto one."""
        from datetime import time

        # Mon/Tue/Wed 07:00 slots already exist from setUp.
        for day in ['Thu', 'Fri']:
            TimeSlot.objects.create(day=day, start_time=time(7, 0), duration_hours=2, slot_type='lec')

        subjects = [
            Subject.objects.create(code=f'X{i}', name=f'Course {i}', units=3)
            for i in range(1, 6)
        ]
        generate_schedule_for_subjects(
            self.student,
            [s.id for s in subjects],
            semester='1st Sem',
            school_year='2025-2026',
        )

        used_days = set(
            StudentSchedule.objects.filter(
                student=self.student, subject__in=subjects
            ).values_list('time_slot__day', flat=True)
        )
        self.assertEqual(len(used_days), 5, f'Expected 5 distinct days, got {sorted(used_days)}')

    def test_regenerate_clears_old_schedules(self):
        # Enroll student in subjects first
        self.student.enrolled_subjects.set([self.subject1, self.subject2, self.subject3])

        # First generation
        generate_schedule_for_subjects(
            self.student,
            [self.subject1.id],
            semester='1st Sem',
            school_year='2025-2026',
        )
        self.assertEqual(StudentSchedule.objects.filter(student=self.student).count(), 1)

        # Regenerate with all enrolled subjects
        regenerate_student_schedule(
            self.student,
            semester='1st Sem',
            school_year='2025-2026',
        )
        # Should have 3 schedules (all enrolled subjects), not 1+3=4
        self.assertEqual(StudentSchedule.objects.filter(student=self.student).count(), 3)

    def test_schedule_api_admin_can_create(self):
        """Admin should be able to create schedule entries."""
        self.client.force_authenticate(user=self.admin)
        slot = TimeSlot.objects.first()
        url = reverse('schedule-list')
        data = {
            'student': self.student.id,
            'subject': self.subject1.id,
            'time_slot': slot.id,
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_schedule_list_is_ordered_chronologically(self):
        """Days must come back Mon..Sun, not alphabetically."""
        from datetime import time

        for day in ['Fri', 'Mon', 'Wed']:
            TimeSlot.objects.create(day=day, start_time=time(13, 0), duration_hours=2, slot_type='lec')
        for index, day in enumerate(['Fri', 'Mon', 'Wed']):
            StudentSchedule.objects.create(
                student=self.student,
                subject=[self.subject1, self.subject2, self.subject3][index],
                time_slot=TimeSlot.objects.get(day=day, start_time=time(13, 0)),
                semester='1st Sem',
                school_year='2025-2026',
            )

        self.client.force_authenticate(user=self.admin)
        res = self.client.get(reverse('schedule-list'))
        days = [r['day'] for r in res.data.get('results', res.data)]
        self.assertEqual(days, ['Mon', 'Wed', 'Fri'])

    def test_schedule_student_can_view_own(self):
        # Create a schedule for the student
        slot = TimeSlot.objects.first()
        StudentSchedule.objects.create(
            student=self.student,
            subject=self.subject1,
            time_slot=slot,
            semester='1st Sem',
            school_year='2025-2026',
        )

        self.client.force_authenticate(user=self.student_user)
        url = reverse('schedule-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)