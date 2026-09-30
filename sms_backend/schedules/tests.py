"""
Tests for schedules app.
Validates automatic conflict-free schedule generation and admin time editing.
"""

from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from schedules.models import StudentSchedule, TimeSlot
from schedules.scheduler import (
    regenerate_all_schedules,
    regenerate_student_schedule,
    schedule_subject,
    slots_overlap,
)
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
        TimeSlot.objects.create(day='Mon', start_time=time(7, 0), end_time=time(9, 0), slot_type='lec')
        TimeSlot.objects.create(day='Mon', start_time=time(9, 0), end_time=time(11, 0), slot_type='lec')
        TimeSlot.objects.create(day='Tue', start_time=time(7, 0), end_time=time(9, 0), slot_type='lec')
        TimeSlot.objects.create(day='Tue', start_time=time(9, 0), end_time=time(11, 0), slot_type='lec')
        TimeSlot.objects.create(day='Wed', start_time=time(7, 0), end_time=time(9, 0), slot_type='lec')

    def test_generate_schedule_assigns_non_conflicting_slots(self):
        """Verify that auto-generated schedules do not have time conflicts."""
        self.student.enrolled_subjects.set([self.subject1, self.subject2, self.subject3])
        results = regenerate_student_schedule(
            self.student, semester='1st Sem', school_year='2025-2026'
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

    def test_shared_subject_meets_at_one_time_for_all_students(self):
        """A course must not meet at different times depending on the student."""
        other = Student.objects.create(
            user=User.objects.create_user(
                username="stu_two", email="stu_two@t.com", password="pw", role=User.ROLE_STUDENT
            ),
            name="Second Student",
            email="stu_two@t.com",
            program="BS CS",
            year_level="1st Year",
        )
        shared = Subject.objects.create(code='SHARED1', name='Shared Subject', units=3)
        self.student.enrolled_subjects.add(shared)
        other.enrolled_subjects.add(shared)

        regenerate_all_schedules(semester='1st Sem', school_year='2025-2026')

        rows = list(
            StudentSchedule.objects.filter(subject=shared).values_list(
                'time_slot_id', flat=True
            )
        )
        self.assertEqual(len(rows), 2, 'both students should be scheduled')
        self.assertEqual(len(set(rows)), 1, 'both students must share one time slot')

    def test_regenerating_one_student_keeps_cohort_time(self):
        """Re-enrolling one student must not move the rest of the class."""
        other = Student.objects.create(
            user=User.objects.create_user(
                username="stu_three", email="stu_three@t.com", password="pw", role=User.ROLE_STUDENT
            ),
            name="Third Student",
            email="stu_three@t.com",
            program="BS CS",
            year_level="1st Year",
        )
        shared = Subject.objects.create(code='SHARED2', name='Another Shared', units=3)
        self.student.enrolled_subjects.add(shared)
        other.enrolled_subjects.add(shared)

        regenerate_all_schedules(semester='1st Sem', school_year='2025-2026')
        before = StudentSchedule.objects.filter(subject=shared).first().time_slot_id

        # Re-enrol this student alone; the cohort time should survive.
        self.student.enrolled_subjects.set([shared])
        regenerate_student_schedule(
            self.student, semester='1st Sem', school_year='2025-2026'
        )

        after = StudentSchedule.objects.filter(subject=shared).first().time_slot_id
        self.assertEqual(before, after)

    def test_generated_schedule_spreads_across_days(self):
        """Successive subjects should land on different days, not pile onto one."""
        # Mon/Tue/Wed 07:00 slots already exist from setUp.
        for day in ['Thu', 'Fri']:
            TimeSlot.objects.create(day=day, start_time=time(7, 0), end_time=time(9, 0), slot_type='lec')

        subjects = [
            Subject.objects.create(code=f'X{i}', name=f'Course {i}', units=3)
            for i in range(1, 6)
        ]
        self.student.enrolled_subjects.set(subjects)
        regenerate_all_schedules(semester='1st Sem', school_year='2025-2026')

        used_days = set(
            StudentSchedule.objects.filter(
                student=self.student, subject__in=subjects
            ).values_list('time_slot__day', flat=True)
        )
        self.assertEqual(len(used_days), 5, f'Expected 5 distinct days, got {sorted(used_days)}')

    def test_regenerate_clears_old_schedules(self):
        # Enroll student in subjects first
        self.student.enrolled_subjects.set([self.subject1, self.subject2, self.subject3])

        # First generation, for one subject only
        schedule_subject(self.subject1, semester='1st Sem', school_year='2025-2026')
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
        for day in ['Fri', 'Mon', 'Wed']:
            TimeSlot.objects.create(day=day, start_time=time(13, 0), end_time=time(15, 0), slot_type='lec')
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


class SubjectEnrollmentTests(APITestCase):
    """An admin can add or remove many students on a subject at once."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="root_sub", email="root_sub@test.com", password="pw"
        )
        self.teacher = User.objects.create_user(
            username="teach_sub", email="teach_sub@test.com", password="pw",
            role=User.ROLE_TEACHER,
        )
        self.subject = Subject.objects.create(code="BULK1", name="Bulk Subject", units=3)
        # Each test class gets a fresh database, so slots must be created here.
        for day in ['Mon', 'Tue', 'Wed']:
            TimeSlot.objects.create(
                day=day, start_time=time(7, 0), end_time=time(9, 0), slot_type='lec'
            )
        self.students = [
            Student.objects.create(
                user=User.objects.create_user(
                    username=f"bulk{i}", email=f"bulk{i}@t.com", password="pw",
                    role=User.ROLE_STUDENT,
                ),
                name=f"Bulk Student {i}",
                email=f"bulk{i}@t.com",
                program="BS CS",
                year_level="1st Year",
            )
            for i in range(1, 4)
        ]
        self.client.force_authenticate(user=self.admin)

    def test_add_multiple_students_to_one_subject(self):
        ids = [s.id for s in self.students]
        res = self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': ids},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 3)
        self.assertEqual(
            set(self.subject.enrolled_students.values_list('id', flat=True)), set(ids)
        )

    def test_added_students_share_one_class_time(self):
        ids = [s.id for s in self.students]
        res = self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': ids, 'semester': '1st Sem', 'school_year': '2025-2026'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data['schedule'])

        rows = list(
            StudentSchedule.objects.filter(subject=self.subject).values_list(
                'time_slot_id', flat=True
            )
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(set(rows)), 1, 'all students must share one slot')

    def test_remove_students_from_subject(self):
        ids = [s.id for s in self.students]
        self.subject.enrolled_students.set(self.students)
        res = self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': [ids[0]], 'remove': True},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 2)
        self.assertNotIn(ids[0], self.subject.enrolled_students.values_list('id', flat=True))

    def test_enrollment_without_term_uses_configured_term(self):
        """Omitting a term must not create a second, empty-semester timetable."""
        from django.conf import settings

        self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': [s.id for s in self.students]},
            format='json',
        )
        rows = StudentSchedule.objects.filter(subject=self.subject)
        self.assertTrue(rows.exists())
        self.assertEqual(
            {r.semester for r in rows}, {settings.CURRENT_SEMESTER}
        )
        self.assertEqual(
            {r.school_year for r in rows}, {settings.CURRENT_SCHOOL_YEAR}
        )
        self.assertFalse(
            StudentSchedule.objects.filter(subject=self.subject, semester='').exists()
        )

    def test_list_enrolled_students(self):
        self.subject.enrolled_students.set(self.students[:2])
        res = self.client.get(reverse('subject-students', kwargs={'pk': self.subject.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)
        self.assertEqual(
            {s['id'] for s in res.data['students']},
            {self.students[0].id, self.students[1].id},
        )

    def test_unknown_student_ids_are_reported(self):
        res = self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': [self.students[0].id, 'STU-99999']},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 1)
        self.assertEqual(res.data['not_found'], ['STU-99999'])

    def test_teacher_cannot_modify_enrollment(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('subject-enroll-students', kwargs={'pk': self.subject.id}),
            {'student_ids': [self.students[0].id]},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class ScheduleAdminTests(APITestCase):
    """Staff can view and change class times through the Django admin."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="root_s", email="root_s@test.com", password="pw"
        )
        self.student_user = User.objects.create_user(
            username="stu_adm", email="stu_adm@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            name="Admin Schedule Student",
            email="stu_adm@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.subject = Subject.objects.create(code="CS301", name="Databases", units=3)
        self.slot = TimeSlot.objects.create(
            day='Mon', start_time=time(7, 0), end_time=time(9, 0), slot_type='lec', label='Period 1'
        )
        self.schedule = StudentSchedule.objects.create(
            student=self.student,
            subject=self.subject,
            time_slot=self.slot,
            semester='1st Sem',
            school_year='2025-2026',
        )
        self.client.force_login(self.admin)

    def test_admin_pages_render(self):
        for name in (
            'admin:schedules_timeslot_changelist',
            'admin:schedules_timeslot_add',
            'admin:schedules_studentschedule_changelist',
            'admin:schedules_studentschedule_add',
        ):
            with self.subTest(view=name):
                res = self.client.get(reverse(name))
                self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_change_form_renders(self):
        res = self.client.get(reverse('admin:schedules_timeslot_change', args=[self.slot.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_change_slot_time(self):
        res = self.client.post(
            reverse('admin:schedules_timeslot_change', args=[self.slot.id]),
            {
                'day': 'Mon',
                'start_time': '09:30',
                'end_time': '12:30',
                'slot_type': 'lab',
                'label': 'Morning Lab',
            },
        )
        self.assertEqual(res.status_code, 302)  # redirect after save

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.start_time, time(9, 30))
        self.assertEqual(self.slot.end_time, time(12, 30))
        self.assertEqual(self.slot.duration_hours, 3)
        self.assertEqual(self.slot.slot_type, 'lab')

    def test_editing_slot_time_moves_assigned_classes(self):
        """Existing schedules point at the slot, so they follow the new time."""
        self.client.post(
            reverse('admin:schedules_timeslot_change', args=[self.slot.id]),
            {
                'day': 'Tue',
                'start_time': '13:00',
                'end_time': '15:00',
                'slot_type': 'lec',
                'label': 'Period 1',
            },
        )
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.time_slot.day, 'Tue')
        self.assertEqual(self.schedule.time_slot.start_time, time(13, 0))
        self.assertEqual(self.schedule.time_slot.end_time, time(15, 0))
        self.assertEqual(StudentSchedule.objects.count(), 1)

    def test_end_time_must_be_after_start_time(self):
        with self.assertRaises(ValidationError):
            TimeSlot.objects.create(
                day='Sun', start_time=time(9, 0), end_time=time(8, 0), slot_type='lec'
            )

    def test_duration_is_derived_from_times(self):
        slot = TimeSlot.objects.create(
            day='Sun', start_time=time(8, 0), end_time=time(11, 30), slot_type='lec'
        )
        self.assertEqual(slot.duration_hours, 4)  # 3.5h rounds half up

    def test_editing_end_time_changes_assigned_classes(self):
        """The class finishes at the time set on the slot, not start + duration."""
        slot = TimeSlot.objects.create(
            day='Sat', start_time=time(9, 0), end_time=time(10, 0), slot_type='lec'
        )
        subject = Subject.objects.create(code='SA101', name='Saturday Subject', units=3)
        schedule = StudentSchedule.objects.create(
            student=self.student,
            subject=subject,
            time_slot=slot,
            semester='1st Sem',
            school_year='2025-2026',
        )

        slot.end_time = time(12, 0)
        slot.save()
        slot.refresh_from_db()
        schedule.refresh_from_db()

        self.assertEqual(schedule.time_slot.end_time, time(12, 0))
        self.assertEqual(slot.duration_hours, 3)

    def test_api_rejects_end_before_start(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            reverse('timeslot-list'),
            {
                'day': 'Sun',
                'start_time': '10:00',
                'end_time': '08:00',
                'slot_type': 'lec',
                'label': 'Bad',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_time', res.data)

    def test_api_accepts_custom_end_time(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            reverse('timeslot-list'),
            {
                'day': 'Sun',
                'start_time': '10:00',
                'end_time': '11:30',
                'slot_type': 'lab',
                'label': 'Short Lab',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['end_time'], '11:30:00')
        self.assertEqual(res.data['duration_hours'], 2)  # derived, read-only

    def test_admin_timeslot_list_is_chronological(self):
        TimeSlot.objects.create(day='Fri', start_time=time(8, 0), end_time=time(9, 0), slot_type='lec')
        TimeSlot.objects.create(day='Tue', start_time=time(8, 0), end_time=time(9, 0), slot_type='lec')
        res = self.client.get(reverse('admin:schedules_timeslot_changelist'))
        days = [obj.day for obj in res.context['cl'].queryset]
        self.assertEqual(days, ['Mon', 'Tue', 'Fri'])

    def test_non_staff_cannot_enter_admin(self):
        self.client.force_login(self.student_user)
        res = self.client.get(reverse('admin:schedules_timeslot_changelist'))
        self.assertEqual(res.status_code, 302)  # redirected away from admin