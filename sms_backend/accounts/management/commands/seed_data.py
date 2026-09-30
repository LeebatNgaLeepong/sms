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

        # 5. Create Sample Grades (University of Antique 1.0-5.0 scale)
        grades_data = [
            # Alice: Excellent grades
            (stu_alice, cs101, Decimal('99.00'), teacher_smith),   # 1.00
            (stu_alice, cs201, Decimal('87.00'), teacher_smith),   # 2.00
            (stu_alice, math101, Decimal('93.00'), teacher_jones),  # 1.50
            # Bob: Mixed grades
            (stu_bob, cs101, Decimal('78.00'), teacher_smith),     # 2.75
            (stu_bob, math101, Decimal('65.00'), teacher_jones),   # 5.00 (Fail)
            (stu_bob, eng101, Decimal('81.00'), teacher_jones),    # 2.50
            # Charlie: Needs improvement
            (stu_charlie, cs101, Decimal('55.00'), teacher_smith), # 5.00 (Fail)
            (stu_charlie, eng101, Decimal('75.00'), teacher_jones),# 3.00 (Pass)
            # Diana
            (stu_diana, math101, Decimal('98.00'), teacher_jones), # 1.00
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

        # 6. Create Sample Time Slots (7:00 AM - 8:00 PM, Mon-Sun)
        from schedules.models import TimeSlot, StudentSchedule
        time_slots_data = [
            # Monday slots
            ('Mon', '07:00', 2, 'lec'), ('Mon', '09:00', 2, 'lec'),
            ('Mon', '11:00', 2, 'lab'), ('Mon', '13:00', 2, 'lec'),
            ('Mon', '15:00', 2, 'lec'), ('Mon', '17:00', 2, 'lab'),
            # Tuesday slots
            ('Tue', '07:00', 2, 'lec'), ('Tue', '09:00', 2, 'lab'),
            ('Tue', '11:00', 2, 'lec'), ('Tue', '13:00', 2, 'lec'),
            ('Tue', '15:00', 2, 'lec'), ('Tue', '17:00', 2, 'lab'),
            # Wednesday slots
            ('Wed', '07:00', 2, 'lec'), ('Wed', '09:00', 2, 'lec'),
            ('Wed', '11:00', 2, 'lab'), ('Wed', '13:00', 2, 'lec'),
            ('Wed', '15:00', 2, 'lec'), ('Wed', '17:00', 2, 'lab'),
            # Thursday slots
            ('Thu', '07:00', 2, 'lec'), ('Thu', '09:00', 2, 'lec'),
            ('Thu', '11:00', 2, 'lab'), ('Thu', '13:00', 2, 'lec'),
            ('Thu', '15:00', 2, 'lec'), ('Thu', '17:00', 2, 'lab'),
            # Friday slots
            ('Fri', '07:00', 2, 'lec'), ('Fri', '09:00', 2, 'lec'),
            ('Fri', '11:00', 2, 'lab'), ('Fri', '13:00', 2, 'lec'),
            ('Fri', '15:00', 2, 'lec'), ('Fri', '17:00', 2, 'lab'),
        ]
        from datetime import time
        for day, start_str, duration, slot_type in time_slots_data:
            h, m = map(int, start_str.split(':'))
            TimeSlot.objects.get_or_create(
                day=day,
                start_time=time(h, m),
                duration_hours=duration,
                slot_type=slot_type,
            )

        self.stdout.write(self.style.SUCCESS("Created sample time slots."))

        # 7. Enroll students in subjects, then generate conflict-free schedules
        enrollment_map = {
            stu_alice: [cs101, cs201, math101, eng101],
            stu_bob: [cs101, math101, eng101, phy101],
            stu_charlie: [cs101, eng101, math101],
            stu_diana: [math101, cs201, phy101],
            stu_edward: [cs101, cs201, eng101, math101],
        }
        for student, subject_list in enrollment_map.items():
            student.enrolled_subjects.set(subject_list)
        self.stdout.write(self.style.SUCCESS("Enrolled students in subjects."))

        from schedules.scheduler import regenerate_student_schedule
        scheduled_total = 0
        for student, subject_list in enrollment_map.items():
            result = regenerate_student_schedule(
                student, semester='1st Sem 2026', school_year='2025-2026'
            )
            scheduled_total += sum(1 for r in result if r['time_slot'] is not None)

        self.stdout.write(
            self.style.SUCCESS(f"Created {scheduled_total} sample schedule entries for students.")
        )
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
