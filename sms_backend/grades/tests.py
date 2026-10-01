"""
Tests for grades app.
Validates business logic:
- Server-side score -> grade_points computation (University of Antique 1.0-5.0 scale)
- Score range constraints (0 to 100)
- Teacher course assignment constraint
- Student read-only isolation
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from grades.models import Grade
from students.models import Student
from subjects.models import Subject

User = get_user_model()


class IncompleteGradeTests(APITestCase):
    """INC replaces the old 4.00 grade and is excluded from averages."""

    def setUp(self):
        self.student = Student.objects.create(
            user=get_user_model().objects.create_user(
                username='inc_user', email='inc_user@t.com', password='pw',
                role=get_user_model().ROLE_STUDENT,
            ),
            name='INC Student',
            email='inc_user@t.com',
            program='BS CS',
            year_level='1st Year',
        )
        self.subject = Subject.objects.create(code='INC101', name='Incomplete', units=3)
        self.other = Subject.objects.create(code='INC102', name='Passed', units=3)
        self.teacher = get_user_model().objects.create_user(
            username='inc_teacher', email='inc_teacher@t.com', password='pw',
            role=get_user_model().ROLE_TEACHER,
        )
        self.subject.instructor = self.teacher
        self.subject.save()

    def test_inc_grade_has_no_points(self):
        grade = Grade.objects.create(
            student=self.student, subject=self.subject,
            is_incomplete=True, recorded_by=self.teacher,
        )
        self.assertEqual(grade.letter, 'INC')
        self.assertIsNone(grade.grade_points)
        self.assertIsNone(grade.score)

    def test_inc_is_excluded_from_gpa_and_gwa(self):
        Grade.objects.create(
            student=self.student, subject=self.other, score=Decimal('99.00'),
            recorded_by=self.teacher,
        )
        before_gpa, before_gwa = self.student.gpa, self.student.gwa

        Grade.objects.create(
            student=self.student, subject=self.subject,
            is_incomplete=True, recorded_by=self.teacher,
        )

        self.assertEqual(self.student.gpa, before_gpa, 'INC must not move GPA')
        self.assertEqual(self.student.gwa, before_gwa, 'INC must not move GWA')
        self.assertEqual(self.student.units_earned, 3, 'INC units are not earned')
        self.assertEqual(self.student.incomplete_count, 1)

    def test_api_marks_grade_incomplete(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('grade-list'),
            {'student': self.student.id, 'subject': self.subject.id, 'is_incomplete': True},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], 'INC')
        self.assertIsNone(res.data['grade_points'])

    def test_api_rejects_neither_score_nor_inc(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('grade-list'),
            {'student': self.student.id, 'subject': self.subject.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('score', res.data)

    def test_api_rejects_score_together_with_inc(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id, 'subject': self.subject.id,
                'score': '90.00', 'is_incomplete': True,
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('score', res.data)

    def test_api_accepts_explicit_null_score_with_inc(self):
        """The UI always sends score: null, which must not 500."""
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': None,
                'is_incomplete': True,
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], 'INC')

    def test_api_accepts_explicit_null_score_on_update(self):
        Grade.objects.create(
            student=self.student, subject=self.subject, score=Decimal('88.00'),
            recorded_by=self.teacher,
        )
        existing = Grade.objects.get(student=self.student, subject=self.subject)
        self.client.force_authenticate(user=self.teacher)
        # Same payload shape the UI sends when editing a grade.
        res = self.client.put(
            reverse('grade-detail', kwargs={'pk': existing.pk}),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': None,
                'is_incomplete': True,
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['letter'], 'INC')

    def test_api_rejects_null_score_without_inc(self):
        self.client.force_authenticate(user=self.teacher)
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': None,
                'is_incomplete': False,
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('score', res.data)

    def test_no_4_grade_point_is_ever_produced(self):
        grade = Grade.objects.create(
            student=self.student, subject=self.other, score=Decimal('75.00'),
            recorded_by=self.teacher,
        )
        self.assertEqual(grade.letter, '3.00')
        self.assertNotEqual(str(grade.grade_points), '4.00')


class ConfigurableScaleTests(APITestCase):
    """The grading bands come from settings, and staff can override them."""

    def setUp(self):
        self.student = Student.objects.create(
            user=get_user_model().objects.create_user(
                username='scale_user', email='scale_user@t.com', password='pw',
                role=get_user_model().ROLE_STUDENT,
            ),
            name='Scale Student',
            email='scale_user@t.com',
            program='BS CS',
            year_level='1st Year',
        )
        self.subject = Subject.objects.create(code='SCL101', name='Scale', units=3)
        self.teacher = get_user_model().objects.create_user(
            username='scale_teacher', email='scale_teacher@t.com', password='pw',
            role=get_user_model().ROLE_TEACHER,
        )
        self.subject.instructor = self.teacher
        self.subject.save()
        self.client.force_authenticate(user=self.teacher)

    def test_scale_endpoint_lists_configured_bands(self):
        res = self.client.get(reverse('grade-scale'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        letters = [b['letter'] for b in res.data['bands']]
        self.assertEqual(letters[0], '1.00')
        self.assertEqual(letters[-1], '5.00', 'scale must end with a catch-all band')
        self.assertEqual(res.data['incomplete'], 'INC')

    def test_manual_grade_bypasses_the_bands(self):
        """A grade with no band, such as 4.00, can be recorded deliberately."""
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': None,
                'manual_points': '4.00',
                'remark': 'Retake, approved by dean',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], '4.00')
        self.assertEqual(res.data['grade_points'], '4.00')
        self.assertEqual(res.data['remark'], 'Retake, approved by dean')

    def test_manual_grade_with_a_band_reuses_that_code(self):
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': None,
                'manual_points': '1.50',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], '1.50')

    def test_manual_grade_and_score_together_are_rejected(self):
        res = self.client.post(
            reverse('grade-list'),
            {
                'student': self.student.id,
                'subject': self.subject.id,
                'score': '90.00',
                'manual_points': '2.00',
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('manual_points', res.data)

    def test_failing_score_falls_to_the_catch_all_band(self):
        grade = Grade.objects.create(
            student=self.student, subject=self.subject, score=Decimal('74.00'),
            recorded_by=self.teacher,
        )
        self.assertEqual(grade.letter, '5.00')
        self.assertEqual(grade.grade_points, Decimal('5.00'))

    def test_manual_grade_is_counted_in_gwa(self):
        Grade.objects.create(
            student=self.student, subject=self.subject, score=Decimal('99.00'),
            recorded_by=self.teacher,
        )
        before = self.student.gwa
        grade = Grade.objects.filter(student=self.student).first()
        grade.manual_points = Decimal('4.00')
        grade.score = None
        grade.save()
        self.assertNotEqual(self.student.gwa, before)


class WeightedAverageTests(APITestCase):
    """GWA weights grade points by subject units; the simple GPA does not."""

    def setUp(self):
        self.student = Student.objects.create(
            user=get_user_model().objects.create_user(
                username='gwa_user', email='gwa_user@t.com', password='pw',
                role=get_user_model().ROLE_STUDENT,
            ),
            name='GWA Student',
            email='gwa_user@t.com',
            program='BS CS',
            year_level='1st Year',
        )
        # 3 units scoring 1.00 and 5 units scoring 3.00
        self.light = Subject.objects.create(code='GWA101', name='Light', units=3)
        self.heavy = Subject.objects.create(code='GWA102', name='Heavy', units=5)
        self.teacher = get_user_model().objects.create_user(
            username='gwa_teacher', email='gwa_teacher@t.com', password='pw',
            role=get_user_model().ROLE_TEACHER,
        )

    def _grade(self, subject, score):
        return Grade.objects.create(
            student=self.student, subject=subject, score=Decimal(score),
            recorded_by=self.teacher,
        )

    def test_gwa_weights_by_units(self):
        self._grade(self.light, '99.00')  # 1.00 points
        self._grade(self.heavy, '76.00')  # 3.00 points
        # (3 * 1.00 + 5 * 3.00) / 8 = 18 / 8 = 2.25
        self.assertEqual(self.student.gwa, 2.25)

    def test_gpa_ignores_units(self):
        self._grade(self.light, '99.00')
        self._grade(self.heavy, '76.00')
        # simple mean of 1.00 and 3.00
        self.assertEqual(self.student.gpa, 2.00)

    def test_gwa_defaults_to_five_without_grades(self):
        self.assertEqual(self.student.gwa, 5.00)
        self.assertEqual(self.student.units_earned, 0)

    def test_units_earned_sums_graded_subjects(self):
        self._grade(self.light, '99.00')
        self.assertEqual(self.student.units_earned, 3)

    def test_gwa_exposed_on_student_api(self):
        self._grade(self.light, '99.00')
        self.client.force_authenticate(user=self.teacher)
        res = self.client.get(reverse('student-detail', kwargs={'pk': self.student.id}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['gwa'], 1.0)
        self.assertEqual(res.data['units_earned'], 3)


class GradeLogicAndAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_g", email="admin_g@test.com", password="pw", role=User.ROLE_ADMIN
        )
        self.teacher1 = User.objects.create_user(
            username="teacher_cs", email="teacher_cs@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.teacher2 = User.objects.create_user(
            username="teacher_math", email="teacher_math@test.com", password="pw", role=User.ROLE_TEACHER
        )
        self.student_user = User.objects.create_user(
            username="student_g", email="student_g@test.com", password="pw", role=User.ROLE_STUDENT
        )
        self.other_student_user = User.objects.create_user(
            username="student_other", email="student_other@test.com", password="pw", role=User.ROLE_STUDENT
        )

        self.student = Student.objects.create(
            user=self.student_user,
            name="Alice Student",
            email="alice_g@test.com",
            program="BS CS",
            year_level="2nd Year",
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            name="Bob Student",
            email="bob_g@test.com",
            program="BS CS",
            year_level="2nd Year",
        )

        self.cs_subject = Subject.objects.create(
            code="CS101",
            name="Intro CS",
            units=3,
            instructor=self.teacher1,
        )
        self.math_subject = Subject.objects.create(
            code="MATH101",
            name="Calculus",
            units=4,
            instructor=self.teacher2,
        )

    def test_score_to_grade_points_computation(self):
        # 99 -> 1.00 (best)
        g1 = Grade.objects.create(
            student=self.student, subject=self.cs_subject, score=Decimal('99.00')
        )
        self.assertEqual(g1.letter, '1.00')
        self.assertEqual(g1.grade_points, Decimal('1.00'))

        # 87 -> 2.00
        g2 = Grade.objects.create(
            student=self.other_student, subject=self.cs_subject, score=Decimal('87.00')
        )
        self.assertEqual(g2.letter, '2.00')
        self.assertEqual(g2.grade_points, Decimal('2.00'))

        # 75 -> 3.00 (passing)
        g3 = Grade.objects.create(
            student=self.student, subject=self.math_subject, score=Decimal('75.00')
        )
        self.assertEqual(g3.letter, '3.00')
        self.assertEqual(g3.grade_points, Decimal('3.00'))

        # 65 -> 5.00 (fail)
        g4 = Grade.objects.create(
            student=self.other_student, subject=self.math_subject, score=Decimal('65.00')
        )
        self.assertEqual(g4.letter, '5.00')
        self.assertEqual(g4.grade_points, Decimal('5.00'))

    def test_server_ignores_client_supplied_letter_and_points(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '75.00',
            'letter': '1.00',           # Client attempts to cheat
            'grade_points': '1.00',     # Client attempts to cheat
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['letter'], '3.00')
        self.assertEqual(Decimal(res.data['grade_points']), Decimal('3.00'))

    def test_score_validation_out_of_range(self):
        self.client.force_authenticate(user=self.admin)
        # Score > 100
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '105.00',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Score < 0
        res2 = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '-10.00',
        })
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_can_only_grade_assigned_subject(self):
        self.client.force_authenticate(user=self.teacher1)
        # Teacher 1 grades assigned CS subject -> Allowed
        res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.cs_subject.id,
            'score': '90.00',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Teacher 1 attempts to grade Math subject (taught by teacher 2) -> Forbidden
        res_fail = self.client.post(reverse('grade-list'), {
            'student': self.other_student.id,
            'subject': self.math_subject.id,
            'score': '90.00',
        })
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subject', res_fail.data)

    def test_student_read_only_isolation(self):
        # Create grade for student 1
        g1 = Grade.objects.create(
            student=self.student, subject=self.cs_subject, score=Decimal('90.00')
        )
        # Create grade for other student
        g2 = Grade.objects.create(
            student=self.other_student, subject=self.cs_subject, score=Decimal('80.00')
        )

        self.client.force_authenticate(user=self.student_user)

        # Student listing grades should only see their own grade
        res = self.client.get(reverse('grade-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], g1.id)

        # Student cannot create a grade
        post_res = self.client.post(reverse('grade-list'), {
            'student': self.student.id,
            'subject': self.math_subject.id,
            'score': '95.00',
        })
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)