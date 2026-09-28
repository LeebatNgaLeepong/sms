# College Student Management System (SMS) — Backend API

Production-ready Django 5.x REST API backend for a College Student Management System featuring role-based authorization (Admin, Teacher, Student), SimpleJWT authentication, automated letter/GPA grade computations, SQLite database, and CORS support.

---

## 🛠 Tech Stack

- **Python**: 3.11+ (Tested on Python 3.14)
- **Django**: 5.2+
- **Django REST Framework (DRF)**: 3.18+
- **Authentication**: `djangorestframework-simplejwt`
- **CORS Support**: `django-cors-headers`
- **Database**: SQLite3 (`db.sqlite3`)

---

## 📁 Project Structure

```text
sms_backend/
│
├── accounts/                      # Custom User model, JWT views, and RBAC permissions
│   ├── management/commands/
│   │   └── seed_data.py           # Database seeding command
│   ├── models.py                  # User model with role choices ('admin', 'teacher', 'student')
│   ├── permissions.py             # DRF permission classes (IsAdmin, GradePermission, etc.)
│   ├── serializers.py             # JWT token and User serializers
│   ├── views.py                   # Login, Refresh, Logout, and /me views
│   ├── urls.py                    # /api/auth/* endpoints
│   └── tests.py                   # Accounts test suite
│
├── students/                      # Student profiles and grade roll-ups
│   ├── models.py                  # Student model (STU-XXXXX auto ID, GPA property)
│   ├── serializers.py             # Student serializers
│   ├── views.py                   # StudentViewSet (/api/students/ & /api/students/{id}/grades/)
│   ├── urls.py
│   └── tests.py
│
├── subjects/                      # Academic courses and teacher assignment
│   ├── models.py                  # Subject model (code, name, units, instructor)
│   ├── serializers.py             # Subject serializers
│   ├── views.py                   # SubjectViewSet (/api/subjects/)
│   ├── urls.py
│   └── tests.py
│
├── grades/                        # Grading system and server-side computation
│   ├── models.py                  # Grade model (score, auto letter, auto grade_points)
│   ├── serializers.py             # Grade validation and teacher course check
│   ├── views.py                   # GradeViewSet (/api/grades/ with ?student=&subject=)
│   ├── urls.py
│   └── tests.py
│
├── dashboard/                     # Institutional summaries and statistics
│   ├── views.py                   # DashboardSummaryView (/api/dashboard/summary/)
│   ├── urls.py
│   └── tests.py
│
├── sms_project/                   # Root Django configuration
│   ├── settings.py                # Installed apps, SimpleJWT, CORS, DRF settings
│   ├── urls.py                    # Root URL router
│   ├── wsgi.py
│   └── asgi.py
│
├── requirements.txt               # Pinned dependencies
├── manage.py
└── db.sqlite3
```

---

## 🚀 Setup & Execution

### 1. Create and Activate Virtual Environment

```bash
# In the sms_backend directory:
python -m venv venv

# Windows (Option A - Run directly without activating):
.\venv\Scripts\python manage.py runserver

# Windows (Option B - Enable script execution for PowerShell if blocked):
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Sample Data (Admin, Teachers, Students, Courses, Grades)

```bash
python manage.py seed_data
```

### 5. Start Development Server

```bash
python manage.py runserver
```
The API is available at `http://127.0.0.1:8000/`.

---

## 👥 Seeded Users & Credentials

| Role | Username | Password | Email | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | `admin@college.edu` | Full CRUD permissions across all resources |
| **Teacher** | `teacher_smith` | `teacher123` | `smith@college.edu` | Instructor for CS101 & CS201 |
| **Teacher** | `teacher_jones` | `teacher123` | `jones@college.edu` | Instructor for MATH101 & ENG101 |
| **Student** | `student_alice` | `student123` | `alice@student.college.edu` | Linked to student `STU-10001` (Alice Guo) |
| **Student** | `student_bob` | `student123` | `bob@student.college.edu` | Linked to student `STU-10002` (Bob Martin) |
| **Student** | `student_charlie`| `student123` | `charlie@student.college.edu`| Linked to student `STU-10003` (Charlie Davis)|

*(Students `STU-10004` and `STU-10005` demonstrate students without login user accounts, adhering to `user=None`).*

---

## 🔐 Role-Based Access Control (RBAC) Matrix

| Endpoint | Admin | Teacher | Student |
| :--- | :--- | :--- | :--- |
| `POST /api/auth/login/` | Anyone | Anyone | Anyone |
| `POST /api/auth/logout/`| Authenticated | Authenticated | Authenticated |
| `GET /api/auth/me/` | Own profile | Own profile | Own profile + student info |
| `GET /api/students/` | View all | View all | View only self |
| `POST /api/students/` | Allowed | 403 Forbidden | 403 Forbidden |
| `GET /api/students/{id}/` | Allowed | Allowed | Allowed only if own ID |
| `PUT /api/students/{id}/` | Allowed | 403 Forbidden | 403 Forbidden |
| `GET /api/students/{id}/grades/` | Allowed | Allowed | Allowed only if own ID |
| `GET /api/subjects/` | Allowed | Allowed | Allowed |
| `POST /api/subjects/` | Allowed | 403 Forbidden | 403 Forbidden |
| `GET /api/grades/` | View all | View all | View only own grades |
| `POST /api/grades/` | Allowed | Allowed only for assigned subject | 403 Forbidden |
| `PUT/PATCH /api/grades/{id}/` | Allowed | Allowed only for assigned subject | 403 Forbidden |
| `GET /api/dashboard/summary/` | Summary stats | Summary stats | Summary stats |

---

## 📊 Business Logic Specifications

### Score to Letter Grade & Grade Points
Computed **strictly on the server side** in `Grade.save()` and `GradeSerializer`:
- **90.00 – 100.00** $\rightarrow$ **A** (4.00 Grade Points)
- **80.00 – 89.99** $\rightarrow$ **B** (3.00 Grade Points)
- **70.00 – 79.99** $\rightarrow$ **C** (2.00 Grade Points)
- **60.00 – 69.99** $\rightarrow$ **D** (1.00 Grade Points)
- **Below 60.00** $\rightarrow$ **F** (0.00 Grade Points)

Scores $< 0$ or $> 100$ are rejected with `HTTP 400 Bad Request`.

### Student GPA Calculation
$$\text{GPA} = \frac{\sum \text{grade\_points}}{\text{total grades}}$$
Rounded to 2 decimal places. Returns `0.00` if student has no recorded grades.

---

## 🧪 Automated Test Suite

Run the full test suite with 20 comprehensive unit and integration tests:

```bash
python manage.py test
```
