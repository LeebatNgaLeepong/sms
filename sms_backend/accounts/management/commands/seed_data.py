"""
Django management command to populate the database with seed data:
- Initial admin user
- Teachers with course assignments
- Students (both with and without login accounts)
- Subjects with credit units
- Grades covering full spectrum (A, B, C, D, F) with computed grade points
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from grades.models import Grade
from students.models import Student
from subjects.models import Subject

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with initial users, subjects, students, and grades."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database..."))

        # 1. Create Admin User
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@college.edu",
                "first_name": "System",
                "last_name": "Administrator",
                "role": User.ROLE_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))

        # 2. Create Teachers
        teacher_smith, created = User.objects.get_or_create(
            username="teacher_smith",
            defaults={
                "email": "smith@college.edu",
                "first_name": "Alan",
                "last_name": "Smith",
                "role": User.ROLE_TEACHER,
                "is_staff": False,
            },
        )
        if created:
            teacher_smith.set_password("teacher123")
            teacher_smith.save()

        teacher_jones, created = User.objects.get_or_create(
            username="teacher_jones",
            defaults={
                "email": "jones@college.edu",
                "first_name": "Sarah",
                "last_name": "Jones",
                "role": User.ROLE_TEACHER,
                "is_staff": False,
            },
        )
        if created:
            teacher_jones.set_password("teacher123")
            teacher_jones.save()

        self.stdout.write(self.style.SUCCESS("Created teachers: teacher_smith, teacher_jones (pw: teacher123)"))

        # 3. Create Subjects
        cs101, _ = Subject.objects.get_or_create(
            code="CS101",
            defaults={
                "name": "Introduction to Computer Science",
                "units": 3,
                "instructor": teacher_smith,
            },
        )
        cs201, _ = Subject.objects.get_or_create(
            code="CS201",
            defaults={
                "name": "Data Structures & Algorithms",
                "units": 4,
                "instructor": teacher_smith,
            },
        )
        math101, _ = Subject.objects.get_or_create(
            code="MATH101",
            defaults={
                "name": "Calculus I",
                "units": 4,
                "instructor": teacher_jones,
            },
        )
        eng101, _ = Subject.objects.get_or_create(
            code="ENG101",
            defaults={
                "name": "Academic Writing and Composition",
                "units": 3,
                "instructor": teacher_jones,
            },
        )
        phy101, _ = Subject.objects.get_or_create(
            code="PHY101",
            defaults={
                "name": "General Physics I",
                "units": 3,
                "instructor": None,
            },
        )
        self.stdout.write(self.style.SUCCESS("Created subjects: CS101, CS201, MATH101, ENG101, PHY101"))

        # 4. Create Students (with and without login accounts)
        # Student 1: Alice (with user account)
        user_alice, created = User.objects.get_or_create(
            username="student_alice",
            defaults={
                "email": "alice@student.college.edu",
                "first_name": "Alice",
                "last_name": "Guo",
                "role": User.ROLE_STUDENT,
            },
        )
        if created:
            user_alice.set_password("student123")
            user_alice.save()

        stu_alice, _ = Student.objects.get_or_create(
            email=user_alice.email,
            defaults={
                "name": "Alice Guo",
                "user": user_alice,
                "program": "BS Computer Science",
                "year_level": "2nd Year",
            },
        )

        # Student 2: Bob (with user account)
        user_bob, created = User.objects.get_or_create(
            username="student_bob",
            defaults={
                "email": "bob@student.college.edu",
                "first_name": "Bob",
                "last_name": "Martin",
                "role": User.ROLE_STUDENT,
            },
        )
        if created:
            user_bob.set_password("student123")
            user_bob.save()

        stu_bob, _ = Student.objects.get_or_create(
            email=user_bob.email,
            defaults={
                "name": "Bob Martin",
                "user": user_bob,
                "program": "BS Computer Science",
                "year_level": "2nd Year",
            },
        )

        # Student 3: Charlie (with user account)
        user_charlie, created = User.objects.get_or_create(
            username="student_charlie",
            defaults={
                "email": "charlie@student.college.edu",
                "first_name": "Charlie",
                "last_name": "Davis",
                "role": User.ROLE_STUDENT,
            },
        )
        if created:
            user_charlie.set_password("student123")
            user_charlie.save()

        stu_charlie, _ = Student.objects.get_or_create(
            email=user_charlie.email,
            defaults={
                "name": "Charlie Davis",
                "user": user_charlie,
                "program": "BS Information Technology",
                "year_level": "1st Year",
            },
        )

        # Student 4: Diana (without user account)
        stu_diana, _ = Student.objects.get_or_create(
            email="diana.prince@college.edu",
            defaults={
                "name": "Diana Prince",
                "user": None,
                "program": "BS Mathematics",
                "year_level": "3rd Year",
            },
        )

        # Student 5: Edward (without user account)
        stu_edward, _ = Student.objects.get_or_create(
            email="edward.norton@college.edu",
            defaults={
                "name": "Edward Norton",
                "user": None,
                "program": "BS Computer Science",
                "year_level": "4th Year",
            },
        )

        self.stdout.write(self.style.SUCCESS("Created students: Alice, Bob, Charlie, Diana, Edward"))

        # 5. Create Sample Grades
        grades_data = [
            # Alice: Excellent grades
            (stu_alice, cs101, Decimal('94.50'), teacher_smith),
            (stu_alice, cs201, Decimal('88.00'), teacher_smith),
            (stu_alice, math101, Decimal('91.00'), teacher_jones),
            # Bob: Mixed grades
            (stu_bob, cs101, Decimal('78.50'), teacher_smith),
            (stu_bob, math101, Decimal('65.00'), teacher_jones),
            (stu_bob, eng101, Decimal('82.00'), teacher_jones),
            # Charlie: Needs improvement
            (stu_charlie, cs101, Decimal('54.00'), teacher_smith),
            (stu_charlie, eng101, Decimal('72.00'), teacher_jones),
            # Diana
            (stu_diana, math101, Decimal('98.00'), teacher_jones),
        ]

        for student, subject, score, teacher in grades_data:
            grade, _ = Grade.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={
                    "score": score,
                    "recorded_by": teacher,
                },
            )

        self.stdout.write(self.style.SUCCESS("Recorded sample grades for students."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
