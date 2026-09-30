# Student Management System (SMS)

A full-stack Student Management System application with Django REST Framework backend and modern React frontend.

## Project Structure

```text
├── sms_backend/       # Django REST Framework backend
└── sms_frontend/      # React + Vite frontend
```

## Features

- **Students** — auto-generated `STU-XXXXX` IDs, programs, year levels, GPA
- **Subjects** — course codes, units, assigned instructor
- **Teachers** — accounts with subject assignments
- **Grades** — scores 0–100, converted server-side to grade points
- **Enrollments** — students enrolled in subjects per semester
- **Schedules** — weekly timetable with automatic conflict-free generation
- **Dashboard** — enrolment counts, average GPA, grade distribution, passing rate

## Grading Scale

Scores are converted server-side using the University of Antique 1.00–5.00 scale
(**lower is better**). 3.00 is the passing mark; 5.00 is a fail.

| Score | Grade | Score | Grade | Score | Grade |
|---|---|---|---|---|---|
| 98–100 | 1.00 | 86–88 | 2.00 | 77–79 | 2.75 |
| 95–97 | 1.25 | 83–85 | 2.25 | 75–76 | 3.00 (pass) |
| 92–94 | 1.50 | 80–82 | 2.50 | below 75 | 5.00 (fail) |

A student with no recorded grades has a GPA of 5.00.

## Schedules

Time slots (day, start time, duration, lecture/lab) are defined once and shared by
every student. Enrolling a student in subjects automatically assigns each subject a
slot with no time conflicts, rotating across days so the whole week is used.

Use **Schedules → Auto-Generate** to rebuild a student's timetable from their current
enrollment. Schedules are keyed by semester and school year, so each term is tracked
separately.

## Getting Started

### 1. Backend Setup (Django)
```bash
cd sms_backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data      # optional: demo users, subjects, grades, schedules
python manage.py runserver
```

### 2. Frontend Setup (React)
```bash
cd sms_frontend
npm install
npm run dev
```

The frontend runs on http://localhost:5173 and proxies `/api` to the Django server
on port 8000, so start the backend first.

## Demo Accounts

Created by `python manage.py seed_data`:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Teacher | `teacher_smith`, `teacher_jones` | `teacher123` |
| Student | `student_alice`, `student_bob`, `student_charlie` | `student123` |

## Tests

```bash
cd sms_backend
python manage.py test
```
