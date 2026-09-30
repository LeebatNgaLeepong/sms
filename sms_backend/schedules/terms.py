"""
Shared term handling.

Semester and school year must come from a fixed list so that unvalidated input
cannot write junk into the schedule and split a timetable across several terms.
"""

from django.conf import settings


class InvalidTerm(ValueError):
    """Raised when a semester or school year is not an allowed option."""

    def __init__(self, field, value):
        self.field = field
        allowed = (
            settings.SEMESTER_CHOICES
            if field == 'semester'
            else settings.SCHOOL_YEAR_CHOICES
        )
        super().__init__(
            f"'{value}' is not a valid {field.replace('_', ' ')}. "
            f'Choose one of: {", ".join(allowed)}'
        )
        self.message = str(self)


def resolve_term(data, semester=None, school_year=None):
    """
    Pull a validated (semester, school_year) pair from request data.

    Missing values fall back to the configured current term so enrollment never
    creates a second timetable under a different term.
    """
    if semester is None:
        semester = data.get('semester') or settings.CURRENT_SEMESTER
    if school_year is None:
        school_year = data.get('school_year') or settings.CURRENT_SCHOOL_YEAR

    semester = str(semester).strip()
    school_year = str(school_year).strip()

    if semester not in settings.SEMESTER_CHOICES:
        raise InvalidTerm('semester', semester)
    if school_year not in settings.SCHOOL_YEAR_CHOICES:
        raise InvalidTerm('school_year', school_year)

    return semester, school_year


def term_options():
    """The term choices the API and UI should offer."""
    return {
        'semesters': list(settings.SEMESTER_CHOICES),
        'school_years': list(settings.SCHOOL_YEAR_CHOICES),
        'current': {
            'semester': settings.CURRENT_SEMESTER,
            'school_year': settings.CURRENT_SCHOOL_YEAR,
        },
    }
