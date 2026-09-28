# Student Management System (SMS)

A full-stack Student Management System application with Django REST Framework backend and modern React frontend.

## Project Structure

```text
├── sms_backend/       # Django REST Framework backend
└── sms_frontend/      # React + Vite frontend
```

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
python manage.py runserver
```

### 2. Frontend Setup (React)
```bash
cd sms_frontend
npm install
npm run dev
```
