"""
Django settings for sms_project.

College Student Management System (SMS) Backend
"""

from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-sms-college-backend-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',

    # Local apps
    'accounts.apps.AccountsConfig',
    'students.apps.StudentsConfig',
    'subjects.apps.SubjectsConfig',
    'grades.apps.GradesConfig',
    'schedules.apps.ScheduleConfig',
    'dashboard.apps.DashboardConfig',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Needs to be at the top for CORS handling
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sms_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# The academic term options enrollment and scheduling may use. Keeping a fixed
# list stops unvalidated free text from writing junk into semester/school_year
# and splitting one timetable across several terms.
SEMESTER_CHOICES = [
    '1st Sem',
    '2nd Sem',
    'Summer',
]

SCHOOL_YEAR_CHOICES = [
    '2024-2025',
    '2025-2026',
    '2026-2027',
    '2027-2028',
]

# The term new enrollments and schedule generation default to.
CURRENT_SEMESTER = '1st Sem'
CURRENT_SCHOOL_YEAR = '2025-2026'

# --- Grading scale -------------------------------------------------------
# Bands are listed highest score first and are the single source of truth for
# turning a score into a grade. Each band needs a minimum score, the grade code
# to record, its grade points, and a description for the UI.
#
# The final band must have 'min': None; it is the catch-all for anything lower
# than the passing band, which is what a failing score gets. To add a band (for
# example 4.00, which the current scale leaves out), insert another entry above
# that catch-all and run makemigrations if the grade codes need a migration.
#
# "INC" is not a band: an unfinished subject is marked separately and carries no
# grade points, so it never appears here.
GRADE_SCALE = [
    {'min': 98.00, 'letter': '1.00', 'points': 1.00, 'label': 'Outstanding', 'description': '98-100'},
    {'min': 95.00, 'letter': '1.25', 'points': 1.25, 'label': 'Excellent', 'description': '95-97'},
    {'min': 92.00, 'letter': '1.50', 'points': 1.50, 'label': 'Very Good', 'description': '92-94'},
    {'min': 89.00, 'letter': '1.75', 'points': 1.75, 'label': 'Good', 'description': '89-91'},
    {'min': 86.00, 'letter': '2.00', 'points': 2.00, 'label': 'Fairly Good', 'description': '86-88'},
    {'min': 83.00, 'letter': '2.25', 'points': 2.25, 'label': 'Fair', 'description': '83-85'},
    {'min': 80.00, 'letter': '2.50', 'points': 2.50, 'label': 'Satisfactory', 'description': '80-82'},
    {'min': 77.00, 'letter': '2.75', 'points': 2.75, 'label': 'Needs Improvement', 'description': '77-79'},
    {'min': 75.00, 'letter': '3.00', 'points': 3.00, 'label': 'Passing', 'description': '75-76'},
    {'min': None, 'letter': '5.00', 'points': 5.00, 'label': 'Failed', 'description': 'Below 75'},
]

# A grade points value at or below this counts as passed. Must match a band.
PASSING_GRADE_POINTS = 3.00

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
