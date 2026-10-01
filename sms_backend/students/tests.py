"""
Tests for students app.
Verifies auto ID generation, GPA computation, and role-based permissions.
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from grades.models import Grade
from students.models import EnrollmentRequest, Student
from subjects.models import Subject

User = get_user_model()


class StudentAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher = User.objects.create_user(
            username="teacher1", email="teacher1@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.student_user_1 = User.objects.create_user(
            username="stu1", email="stu1@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student_user_2 = User.objects.create_user(
            username="stu2", email="stu2@test.com", password="pw", role=User.ROLE_STUDENT
        )

        self.student1 = Student.objects.create(
            user=self.student_user_1,
            name="Student One",
            email="stu1@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.student2 = Student.objects.create(
            user=self.student_user_2,
            name="Student Two",
            email="stu2@test.com",
            program="BS IT",
            year_level="2nd Year",
        )

        self.subject = Subject.objects.create(
            code="CS101",
            name="Intro CS",
            units=3,
            instructor=self.teacher,
        )

    def test_student_auto_id_format(self):
        self.assertTrue(self.student1.id.startswith('STU-'))

    def test_admin_can_create_student(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-list')
        data = {
            'name': 'New Student',
            'email': 'newstu@test.com',
            'program': 'BS Math',
            'year_level': '1st Year',
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['id'].startswith('STU-'))

    def test_teacher_cannot_create_student(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('student-list')
        data = {'name': 'Teacher Student', 'email': 'tstu@test.com', 'program': 'BS', 'year_level': '1st'}
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_only_view_own_profile(self):
        self.client.force_authenticate(user=self.student_user_1)

        # Listing only returns student 1
        res = self.client.get(reverse('student-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Results inside pagination
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.student1.id)

        # Accessing own detail succeeds
        res_own = self.client.get(reverse('student-detail', kwargs={'pk': self.student1.id}))
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)

        # Accessing other student detail is forbidden (403 or 404)
        res_other = self.client.get(reverse('student-detail', kwargs={'pk': self.student2.id}))
        self.assertIn(res_other.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_student_grades_endpoint(self):
        # Create grade for student 1
        Grade.objects.create(
            student=self.student1,
            subject=self.subject,
            score=Decimal('99.00'),
            recorded_by=self.teacher,
        )

        self.client.force_authenticate(user=self.student_user_1)
        url = reverse('student-grades', kwargs={'pk': self.student1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # GPA for 99.00 should be 1.00 on University of Antique scale
        self.assertEqual(res.data['gpa'], 1.0)
        self.assertEqual(len(res.data['grades']), 1)
        self.assertEqual(res.data['grades'][0]['letter'], '1.00')

    def test_gpa_returns_5_when_no_grades(self):
        """Students with no grades should have GPA of 5.00 (fail) on Antique scale."""
        self.assertEqual(self.student2.gpa, 5.00)


class EnrollmentRequestTests(APITestCase):
    """
    A student asks to add a subject; the teacher who teaches it decides.
    """

    def setUp(self):
        from datetime import time

        from schedules.models import TimeSlot

        self.admin = User.objects.create_superuser(
            username='req_admin', email='req_admin@t.com', password='pw'
        )
        self.teacher = User.objects.create_user(
            username='req_teacher', email='req_teacher@t.com', password='pw',
            role=User.ROLE_TEACHER,
        )
        self.other_teacher = User.objects.create_user(
            username='req_teacher2', email='req_teacher2@t.com', password='pw',
            role=User.ROLE_TEACHER,
        )
        self.student_user = User.objects.create_user(
            username='req_student', email='req_student@t.com', password='pw',
            role=User.ROLE_STUDENT,
        )
        self.other_user = User.objects.create_user(
            username='req_student2', email='req_student2@t.com', password='pw',
            role=User.ROLE_STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user, name='Request Student', email='req_student@t.com',
            program='BS CS', year_level='2nd Year',
        )
        self.other_student = Student.objects.create(
            user=self.other_user, name='Other Student', email='req_student2@t.com',
            program='BS CS', year_level='2nd Year',
        )
        self.subject = Subject.objects.create(
            code='REQ101', name='Requested Subject', units=3, instructor=self.teacher
        )
        self.taken = Subject.objects.create(
            code='TAKEN1', name='Already Taken', units=3, instructor=self.teacher
        )
        self.student.enrolled_subjects.add(self.taken)
        for day in ['Mon', 'Tue', 'Wed']:
            TimeSlot.objects.create(
                day=day, start_time=time(7, 0), end_time=time(9, 0), slot_type='lec'
            )

    def _request(self, **kwargs):
        payload = {
            'student': self.student.id,
            'subject': self.subject.id,
            'semester': '1st Sem',
            'school_year': '2025-2026',
            'reason': 'I need this for my major.',
        }
        payload.update(kwargs)
        return payload

    def test_student_can_file_a_request(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], 'pending')
        self.assertEqual(res.data['student'], self.student.id)

    def test_student_cannot_request_for_someone_else(self):
        """Posting another student's id is coerced to the requester, not honoured."""
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(
            reverse('enrollment-request-list'),
            self._request(student=self.other_student.id),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            res.data['student'], self.student.id,
            'the request must belong to the requester, never the id they posted',
        )
        self.assertFalse(EnrollmentRequest.objects.filter(
            student=self.other_student
        ).exists())

    def test_teacher_and_admin_cannot_file_requests(self):
        for user in (self.teacher, self.admin):
            self.client.force_authenticate(user=user)
            res = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, user.username)

    def test_cannot_request_a_subject_already_enrolled(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(
            reverse('enrollment-request-list'),
            self._request(subject=self.taken.id),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subject', res.data)

    def test_cannot_file_two_pending_requests_for_same_subject(self):
        self.client.force_authenticate(user=self.student_user)
        payload = self._request()
        self.assertEqual(
            self.client.post(reverse('enrollment-request-list'), payload, format='json').status_code,
            status.HTTP_201_CREATED,
        )
        again = self.client.post(reverse('enrollment-request-list'), payload, format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_unknown_semester(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(
            reverse('enrollment-request-list'),
            self._request(semester='Ninth Term'),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('semester', res.data)

    def test_approving_enrolls_and_schedules(self):
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        request_id = created.data['id']

        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('enrollment-request-decision', kwargs={'pk': request_id}),
            {'decision': 'approved'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'approved')

        self.assertTrue(self.student.enrolled_subjects.filter(id=self.subject.id).exists())
        # Both enrolled subjects now have a timetable entry.
        self.assertEqual(self.student.schedules.count(), 2)

    def test_rejecting_does_not_enroll(self):
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        request_id = created.data['id']

        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('enrollment-request-decision', kwargs={'pk': request_id}),
            {'decision': 'rejected', 'note': 'Class is full.'},
            format='json',
        )
        self.assertEqual(res.data['status'], 'rejected')
        self.assertFalse(self.student.enrolled_subjects.filter(id=self.subject.id).exists())

    def test_unrelated_teacher_cannot_decide(self):
        """A 404 is correct here: an unrelated teacher must not learn it exists."""
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')

        self.client.force_authenticate(user=self.other_teacher)
        res = self.client.post(
            reverse('enrollment-request-decision', kwargs={'pk': created.data['id']}),
            {'decision': 'approved'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(self.student.enrolled_subjects.filter(id=self.subject.id).exists())

    def test_student_cannot_decide_their_own_request(self):
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        res = self.client.post(
            reverse('enrollment-request-decision', kwargs={'pk': created.data['id']}),
            {'decision': 'approved'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_decide_twice(self):
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        self.client.force_authenticate(user=self.teacher)
        url = reverse('enrollment-request-decision', kwargs={'pk': created.data['id']})
        self.assertEqual(
            self.client.post(url, {'decision': 'approved'}, format='json').status_code,
            status.HTTP_200_OK,
        )
        again = self.client.post(url, {'decision': 'rejected'}, format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_students_only_see_their_own_requests(self):
        self.client.force_authenticate(user=self.student_user)
        self.client.post(reverse('enrollment-request-list'), self._request(), format='json')

        self.client.force_authenticate(user=self.other_user)
        res = self.client.get(reverse('enrollment-request-list'))
        self.assertEqual(res.data['count'], 0)

    def test_teacher_sees_requests_for_their_subjects_only(self):
        self.client.force_authenticate(user=self.student_user)
        self.client.post(reverse('enrollment-request-list'), self._request(), format='json')

        self.client.force_authenticate(user=self.teacher)
        mine = self.client.get(reverse('enrollment-request-list'))
        self.assertEqual(mine.data['count'], 1)

        self.client.force_authenticate(user=self.other_teacher)
        theirs = self.client.get(reverse('enrollment-request-list'))
        self.assertEqual(theirs.data['count'], 0)

    def test_admin_can_decide(self):
        self.client.force_authenticate(user=self.student_user)
        created = self.client.post(reverse('enrollment-request-list'), self._request(), format='json')
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            reverse('enrollment-request-decision', kwargs={'pk': created.data['id']}),
            {'decision': 'approved'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class MessageThreadTests(APITestCase):
    """
    Students and teachers can message each other, and nobody else.
    """

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='msg_admin', email='msg_admin@t.com', password='pw'
        )
        self.teacher = User.objects.create_user(
            username='msg_teacher', email='msg_teacher@t.com', password='pw',
            role=User.ROLE_TEACHER,
        )
        self.other_teacher = User.objects.create_user(
            username='msg_teacher2', email='msg_teacher2@t.com', password='pw',
            role=User.ROLE_TEACHER,
        )
        self.student_user = User.objects.create_user(
            username='msg_student', email='msg_student@t.com', password='pw',
            role=User.ROLE_STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user, name='Messaging Student', email='msg_student@t.com',
            program='BS CS', year_level='2nd Year',
        )
        self.subject = Subject.objects.create(
            code='MSG101', name='Messaging Subject', units=3, instructor=self.teacher
        )

    def _start_as_student(self):
        self.client.force_authenticate(user=self.student_user)
        return self.client.post(
            reverse('thread-list'),
            {'counterpart': self.teacher.id, 'subject': self.subject.id},
            format='json',
        )

    def test_student_starts_thread_with_teacher(self):
        res = self._start_as_student()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['counterpart_name'], self.teacher.username)
        self.assertEqual(res.data['unread_count'], 0)

    def test_starting_twice_reuses_the_thread(self):
        first = self._start_as_student()
        second = self._start_as_student()
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['id'], second.data['id'])

    def test_student_cannot_start_thread_with_another_student(self):
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(
            reverse('thread-list'),
            {'counterpart': self.teacher.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        other_student_user = User.objects.create_user(
            username='msg_student2', email='msg_student2@t.com', password='pw',
            role=User.ROLE_STUDENT,
        )
        self.client.force_authenticate(user=other_student_user)
        res = self.client.post(
            reverse('thread-list'),
            {'counterpart': self.student.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_start_a_thread(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            reverse('thread-list'),
            {'counterpart': self.student.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_replies_in_the_student_thread(self):
        thread_id = self._start_as_student().data['id']

        self.client.force_authenticate(user=self.student_user)
        self.client.post(
            reverse('thread-messages', kwargs={'pk': thread_id}),
            {'body': 'May I join CS101?'},
            format='json',
        )

        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('thread-messages', kwargs={'pk': thread_id}),
            {'body': 'Yes, fill out the form.'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        thread = self.client.get(reverse('thread-messages', kwargs={'pk': thread_id}))
        bodies = [m['body'] for m in thread.data['messages']]
        self.assertEqual(bodies, ['May I join CS101?', 'Yes, fill out the form.'])

    def test_empty_message_is_rejected(self):
        thread_id = self._start_as_student().data['id']
        self.client.force_authenticate(user=self.student_user)
        res = self.client.post(
            reverse('thread-messages', kwargs={'pk': thread_id}),
            {'body': '   '},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unrelated_teacher_cannot_read_thread(self):
        """404 is correct: an unrelated teacher must not learn the thread exists."""
        thread_id = self._start_as_student().data['id']
        self.client.force_authenticate(user=self.other_teacher)
        res = self.client.get(reverse('thread-messages', kwargs={'pk': thread_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unread_count_and_mark_as_read(self):
        thread_id = self._start_as_student().data['id']
        self.client.force_authenticate(user=self.student_user)
        self.client.post(
            reverse('thread-messages', kwargs={'pk': thread_id}),
            {'body': 'Hello'},
            format='json',
        )

        # The teacher has one unread message from the student.
        self.client.force_authenticate(user=self.teacher)
        listing = self.client.get(reverse('thread-list'))
        self.assertEqual(listing.data['count'], 1)
        self.assertEqual(listing.data['results'][0]['unread_count'], 1)

        # Reading the conversation clears it.
        self.client.get(reverse('thread-messages', kwargs={'pk': thread_id}))
        listing = self.client.get(reverse('thread-list'))
        self.assertEqual(listing.data['results'][0]['unread_count'], 0)

    def test_students_only_see_their_own_threads(self):
        self._start_as_student()
        other_student_user = User.objects.create_user(
            username='msg_student3', email='msg_student3@t.com', password='pw',
            role=User.ROLE_STUDENT,
        )
        self.client.force_authenticate(user=other_student_user)
        res = self.client.get(reverse('thread-list'))
        self.assertEqual(res.data['count'], 0)

    def test_teacher_starts_thread_with_student(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('thread-list'),
            {'counterpart': self.student.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['counterpart_role'], 'student')


class EnrollmentScheduleTests(APITestCase):
    """Enrolling a student should auto-generate a conflict-free schedule."""

    def setUp(self):
        from datetime import time

        from schedules.models import TimeSlot

        self.admin = User.objects.create_user(
            username="admin_enroll", email="admin_enroll@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.student_user = User.objects.create_user(
            username="stu_enroll", email="stu_enroll@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.student = Student.objects.create(
            user=self.student_user,
            name="Enroll Student",
            email="stu_enroll@test.com",
            program="BS CS",
            year_level="1st Year",
        )
        self.subject_a = Subject.objects.create(code="CS201", name="Data Structures", units=4)
        self.subject_b = Subject.objects.create(code="MATH201", name="Calculus", units=4)

        # Two non-overlapping slots are enough to schedule both subjects.
        TimeSlot.objects.create(day='Mon', start_time=time(7, 0), end_time=time(9, 0), slot_type='lec')
        TimeSlot.objects.create(day='Mon', start_time=time(9, 0), end_time=time(11, 0), slot_type='lec')

    def test_enroll_auto_generates_schedules(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 2)
        self.assertEqual(res.data['scheduled_count'], 2)

        schedules = self.student.schedules.all()
        self.assertEqual(schedules.count(), 2)
        self.assertEqual({s.time_slot.day for s in schedules}, {'Mon'})

    def test_enroll_accepts_repeated_form_fields(self):
        """Form-encoded requests repeat subject_ids, so every id must be kept."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
        }, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['enrolled_count'], 2)
        self.assertEqual(self.student.enrolled_subjects.count(), 2)
        self.assertEqual(self.student.schedules.count(), 2)

    def test_enroll_replaces_previous_schedule(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})

        self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')
        self.assertEqual(self.student.schedules.count(), 2)

        # Re-enrolling with a single subject should not leave stale schedules.
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')
        self.assertEqual(res.data['scheduled_count'], 1)
        self.assertEqual(self.student.schedules.count(), 1)

    def test_enroll_rolls_back_when_scheduling_fails(self):
        """A scheduler failure must not leave the student's subjects changed."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        self.client.post(url, {
            'subject_ids': [self.subject_a.id, self.subject_b.id],
            'semester': '1st Sem',
            'school_year': '2025-2026',
        }, format='json')
        self.assertEqual(self.student.enrolled_subjects.count(), 2)

        with patch(
            'schedules.scheduler.regenerate_student_schedule',
            side_effect=RuntimeError('scheduler exploded'),
        ):
            res = self.client.post(url, {
                'subject_ids': [self.subject_a.id],
                'semester': '1st Sem',
                'school_year': '2025-2026',
            }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # The internal error text must not be handed back to the client.
        self.assertNotIn('scheduler exploded', str(res.data))
        # Enrollment and schedules both stay on the previous, consistent state.
        self.assertEqual(self.student.enrolled_subjects.count(), 2)
        self.assertEqual(self.student.schedules.count(), 2)

    def test_enroll_rejects_non_numeric_subject_ids(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {'subject_ids': ['abc']}, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Not a raw database error leaking through to the response.
        self.assertNotIn('expected a number', str(res.data))
        self.assertEqual(self.student.enrolled_subjects.count(), 0)

    def test_enroll_reports_unknown_subject_ids(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('student-enroll', kwargs={'pk': self.student.id})
        res = self.client.post(url, {
            'subject_ids': [self.subject_a.id, 999999],
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['not_found'], ['999999'])
        self.assertEqual(res.data['enrolled_count'], 1)