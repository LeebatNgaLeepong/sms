# Student Management System (SMS)

A full-stack Student Management System application with Django REST Framework backend and modern React frontend.

## Project Structure

```text
├── sms_backend/       # Django REST Framework backend
└── sms_frontend/      # React + Vite frontend
```

## Subject requests

Students do not edit their own load directly. They file a **subject request** and
the instructor for that subject (or an admin) approves or rejects it. Approving
enrolls the student and rebuilds their timetable, so the new class gets a real
slot automatically.

- **Students** — request a subject, give a reason, and withdraw a pending request.
  They cannot request a subject they already take, or file a second pending
  request for the same subject and term.
- **Teachers** — see requests for the subjects they teach and decide on them.
- **Admins** — see every request and can decide any of them.

A teacher who does not teach that subject gets a 404 rather than a 403, so an
unrelated teacher cannot even tell the request exists.

## Messaging

Students and teachers can hold a private conversation. One thread per student and
teacher pair, optionally tagged with a subject.

- Starting a conversation with someone you already have a thread with reuses it.
- Only the two participants can read or post; unrelated teachers and admins are
  excluded. Admins can list conversations for oversight but cannot post into them.
- Unread counts are per participant, and reading a conversation clears them.

## Academic Terms

Semester and school year are chosen from dropdowns, never typed. The options come
from `SEMESTER_CHOICES` / `SCHOOL_YEAR_CHOICES` in `sms_project/settings.py` and
are served by `GET /api/terms/`, so the UI and the API can never disagree. An
unrecognised value is rejected instead of being stored, and the sidebar always
shows the current term.

## Sections

A **section** is one class group of a subject, e.g. `CS101-A`. Sections are what
actually meet, so two sections of the same subject can run at different times and
concurrently without clashing. A student takes one section of a subject per term.

- **Subjects page → Sections column** — add, remove, and set capacity and
  instructor for a subject's sections.
- Sections show `enrolled/capacity`, so an over-subscribed section is obvious.
- Add or remove several students from a section in one action; the section is
  then scheduled once for its whole roster.
- Subjects without sections still work: they are scheduled as a whole.

## Grades and GWA

Scores 0–100 are converted server-side to the University of Antique 1.00–5.00
scale (lower is better). 3.00 passes, 5.00 is a fail, and **INC** marks a subject
that is not finished — it carries no grade points and is excluded from averages.

Two figures are reported, and they differ on purpose:

- **GPA** — the simple mean of grade points.
- **GWA (General Weighted Average)** — grade points weighted by subject units:
  `sum(grade_points × units) / sum(units)`. This is the figure the university
  records, and it is what the student list, student page, and dashboard show.

A student with no graded subjects has 5.00 for both.

### Configuring the scale

The bands live in `GRADE_SCALE` in `sms_project/settings.py`, highest score first,
and are the single source of truth. To add a band (for example **4.00**, which
the default scale leaves out), insert an entry above the catch-all band:

```python
{'min': 74.00, 'letter': '4.00', 'points': 4.00, 'label': 'Conditional', 'description': '70-74'},
{'min': None, 'letter': '5.00', 'points': 5.00, 'label': 'Failed', 'description': 'Below 70'},
```

The last band must keep `'min': None` so any low score still receives a grade.
`GET /api/grades/scale/` serves the configured bands, so the UI always offers
exactly the grades the backend will record.

### Manual grades and remarks

Staff can set grade points directly instead of a score, which is how you record a
grade the scale has no band for — such as a **4.00** — or a retake outcome. A
score and a manual grade cannot both be set. Every grade also takes an optional
remark, and grades recorded outside the configured bands still appear in the
dashboard distribution rather than disappearing from it.

## Features

- **Students** — auto-generated `STU-XXXXX` IDs, programs, year levels, GWA
- **Subjects** — course codes, units, sections, assigned instructor
- **Teachers** — accounts with subject and section assignments
- **Grades** — scores 0–100, converted server-side to grade points
- **Enrollments** — students enrolled in subjects and sections per term
- **Subject requests** — students ask to add a subject; staff approve or reject
- **Messaging** — private student-teacher conversations
- **Schedules** — weekly timetable with automatic conflict-free generation
- **Dashboard** — enrolment counts, average GWA, grade distribution, passing rate

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

Time slots (day, start time, end time, lecture/lab) are defined once and shared by
every student. Set the start and end times directly; the duration shown in the UI is
derived from them. Enrolling a student in subjects automatically assigns each subject
a slot with no time conflicts, rotating across days so the whole week is used.

Use **Schedules → Auto-Generate** to rebuild a student's timetable from their current
enrollment. Schedules are keyed by semester and school year, so each term is tracked
separately.

### Enrolling students in a subject

A course meets at **one time per term**, shared by every student enrolled in it.
Adding a student therefore never moves the rest of the cohort — if the existing
time clashes for the new student, the whole subject is rescheduled to a time that
is free for all of them.

- **Subjects page → Students column** — tick students and enrol or remove them in
  one action, instead of visiting each student separately. The subject is
  scheduled for the whole cohort automatically.
- **Student page → Manage Enrollment** — set one student's subjects; shared
  subjects keep the time the rest of the class is in.
- **Schedules → Auto-Generate** — rebuild every subject for the term.

New enrollments default to the term configured as `CURRENT_SEMESTER` /
`CURRENT_SCHOOL_YEAR` in `sms_project/settings.py`, so schedules do not end up
split across several terms. Pass `semester` and `school_year` to override.

### Editing times in the Django admin

Superusers can also manage times and schedule entries at
http://localhost:8000/admin/schedules/. Use `python manage.py createsuperuser` if you
do not have one yet.

- **Time slots** — day, start time, end time, lecture/lab, and label are all editable.
  Changing a slot's times moves every class already assigned to that slot, so all
  students using it are rescheduled together. Deleting a slot instead removes the
  schedule entries that referenced it. The end time must be after the start time;
  duration is derived and not edited directly.
- **Schedule entries** — assign or reassign a student, subject, slot, and term.
  Both lists are ordered chronologically (Monday to Sunday) and filterable by day and
  term.

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
