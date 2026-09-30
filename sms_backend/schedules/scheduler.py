"""
Schedule generation utilities.

A course meets at one time per term, shared by every student enrolled in it, so
scheduling is driven from the subject outwards rather than per student. Slot
selection still respects each individual student's other classes, so a subject
only takes a time that is free for all of its students.
"""

from .models import DAY_ORDER, StudentSchedule, TimeSlot


def slot_sort_key(slot):
    """Sort slots by real weekday order, then by start time."""
    try:
        day_index = DAY_ORDER.index(slot.day)
    except ValueError:
        day_index = len(DAY_ORDER)
    return (day_index, slot.start_time)


def order_slots_by_preference(slots, start_offset=0):
    """
    Return slots grouped by day, starting from `start_offset` and wrapping around.
    Rotating the day order lets successive subjects land on different days.
    """
    if not slots:
        return []

    days = [d for d in DAY_ORDER if any(s.day == d for s in slots)]
    if not days:
        return sorted(slots, key=slot_sort_key)

    grouped = {
        day: sorted((s for s in slots if s.day == day), key=lambda s: s.start_time)
        for day in days
    }
    ordered = []
    for step in range(len(days)):
        ordered.extend(grouped[days[(start_offset + step) % len(days)]])
    return ordered


def slots_overlap(slot_a, slot_b):
    """
    Return True if two time slots overlap in time on the same day.
    """
    if slot_a.day != slot_b.day:
        return False
    a_start, a_end = slot_a.start_time, slot_a.end_time
    b_start, b_end = slot_b.start_time, slot_b.end_time
    # Overlap if one starts before the other ends
    return a_start < b_end and b_start < a_end


def get_student_busy_slots(student, semester=None, school_year=None, exclude_subject=None):
    """Return the time slots a student is already scheduled in for the term."""
    existing = StudentSchedule.objects.filter(
        student=student,
        semester=semester,
        school_year=school_year,
    ).select_related('time_slot')
    if exclude_subject is not None:
        existing = existing.exclude(subject=exclude_subject)
    return {sched.time_slot for sched in existing}


def subject_students(subject):
    return list(subject.enrolled_students.all())


def section_students(section):
    return list(section.students.all())


def subject_busy_slots(subject, semester=None, school_year=None, extra_students=None):
    """
    Slots that are taken by some other class, for any student in this subject.

    A slot is only usable by this subject if it is free for every one of its
    students, so the union of all their other classes is what matters.
    """
    students = list(subject_students(subject))
    if extra_students:
        known = {s.id for s in students}
        students.extend(s for s in extra_students if s.id not in known)
    if not students:
        return set()

    busy = set()
    schedules = StudentSchedule.objects.filter(
        student__in=students,
        semester=semester,
        school_year=school_year,
    ).exclude(subject=subject).select_related('time_slot')
    for sched in schedules:
        busy.add(sched.time_slot)
    return busy


def section_busy_slots(section, semester=None, school_year=None):
    """
    Slots taken by another class for any student in this section.

    Schedules belonging to other sections of the same subject are treated as
    available, since concurrent sections of one course are allowed.
    """
    students = section_students(section)
    if not students:
        return set()

    busy = set()
    schedules = StudentSchedule.objects.filter(
        student__in=students,
        semester=semester,
        school_year=school_year,
    ).exclude(section=section).select_related('time_slot')
    for sched in schedules:
        if sched.section_id is None and sched.subject_id != section.subject_id:
            busy.add(sched.time_slot)
        elif sched.section_id != section.id:
            busy.add(sched.time_slot)
    return busy


def subject_rotation_index(subject):
    """Position of the subject among scheduled subjects, used to spread days."""
    from subjects.models import Subject

    ids = list(
        Subject.objects.filter(enrolled_students__isnull=False)
        .distinct()
        .order_by('code')
        .values_list('id', flat=True)
    )
    try:
        return ids.index(subject.id)
    except ValueError:
        return 0


def section_rotation_index(section):
    """Position of the section among sections, used to spread days."""
    from .models import Section

    ids = list(
        Section.objects.filter(students__isnull=False)
        .distinct()
        .order_by('subject__code', 'code')
        .values_list('id', flat=True)
    )
    try:
        return ids.index(section.id)
    except ValueError:
        return subject_rotation_index(section.subject)


def find_slot_for_subject(subject, semester=None, school_year=None):
    """
    Choose one time slot for a subject that is free for all of its students.

    The slot the subject already uses is preferred so regenerating one student
    does not needlessly move a class the rest of the cohort is in.
    """
    busy = subject_busy_slots(subject, semester, school_year)

    current = (
        StudentSchedule.objects.filter(
            subject=subject,
            semester=semester,
            school_year=school_year,
        )
        .exclude(time_slot__isnull=True)
        .select_related('time_slot')
        .first()
    )

    candidates = []
    if current is not None:
        candidates.append(current.time_slot)
    candidates.extend(
        order_slots_by_preference(
            sorted(TimeSlot.objects.all(), key=slot_sort_key),
            start_offset=subject_rotation_index(subject),
        )
    )

    for slot in candidates:
        if all(not slots_overlap(slot, taken) for taken in busy):
            return slot
    return None


def schedule_subject(subject, semester='', school_year=''):
    """
    Assign one time slot to a subject for every student enrolled in it.

    Any previously assigned rows for this subject and term are replaced, which
    keeps every student of the subject on the same slot.
    """
    students = subject_students(subject)
    if not students:
        StudentSchedule.objects.filter(
            subject=subject, semester=semester, school_year=school_year
        ).delete()
        return None

    slot = find_slot_for_subject(subject, semester, school_year)
    if slot is None:
        return None

    # These students may already sit in a section of this subject; that row has
    # to go before a subject-level row can be created.
    StudentSchedule.objects.filter(
        student__in=students,
        subject=subject,
        semester=semester,
        school_year=school_year,
    ).exclude(section__isnull=True).delete()

    StudentSchedule.objects.filter(
        subject=subject,
        semester=semester,
        school_year=school_year,
        section__isnull=True,
    ).delete()
    StudentSchedule.objects.bulk_create([
        StudentSchedule(
            student=student,
            subject=subject,
            time_slot=slot,
            semester=semester,
            school_year=school_year,
        )
        for student in students
    ])
    return slot


def find_slot_for_section(section, semester=None, school_year=None):
    """
    Choose one time slot for a section that is free for all of its students.

    Sections of the same subject may run concurrently, so only classes outside
    this subject's sections block a slot.
    """
    busy = section_busy_slots(section, semester, school_year)

    current = (
        StudentSchedule.objects.filter(
            section=section, semester=semester, school_year=school_year
        )
        .exclude(time_slot__isnull=True)
        .select_related('time_slot')
        .first()
    )

    candidates = []
    if current is not None:
        candidates.append(current.time_slot)
    candidates.extend(
        order_slots_by_preference(
            sorted(TimeSlot.objects.all(), key=slot_sort_key),
            start_offset=section_rotation_index(section),
        )
    )

    for slot in candidates:
        if all(not slots_overlap(slot, taken) for taken in busy):
            return slot
    return None


def schedule_section(section, semester='', school_year=''):
    """
    Assign one time slot to a section for every student in it.

    Returns the chosen slot, or None when the section has no students or no
    slot is free for all of them.
    """
    students = section_students(section)
    if not students:
        return None

    slot = find_slot_for_section(section, semester, school_year)
    if slot is None:
        return None

    # A student can only take one section of a subject in a term. Drop any row
    # they hold for this subject in another section, so moving them works.
    StudentSchedule.objects.filter(
        student__in=students,
        subject=section.subject,
        semester=semester,
        school_year=school_year,
    ).exclude(section=section).delete()

    StudentSchedule.objects.filter(
        section=section, semester=semester, school_year=school_year
    ).delete()
    StudentSchedule.objects.bulk_create([
        StudentSchedule(
            student=student,
            subject=section.subject,
            section=section,
            time_slot=slot,
            semester=semester,
            school_year=school_year,
        )
        for student in students
    ])
    return slot


def regenerate_student_schedule(student, semester='', school_year=''):
    """
    Rebuild a student's schedule for a term from their enrolled subjects and
    section memberships.

    For each class the student shares with others, the time the rest of the
    group already has is reused when it is free for this student; otherwise the
    whole class is rescheduled so its members stay on the same slot.

    Returns a list of dicts: [{'subject': subject, 'time_slot': slot or None}]
    """
    results = []

    StudentSchedule.objects.filter(
        student=student, semester=semester, school_year=school_year
    ).delete()

    # Sections take priority: they are the real class the student sits in.
    for section in student.sections.all():
        cohort_slot = (
            StudentSchedule.objects.filter(
                section=section, semester=semester, school_year=school_year
            )
            .exclude(student=student)
            .exclude(time_slot__isnull=True)
            .select_related('time_slot')
            .first()
        )
        if cohort_slot is not None:
            busy = get_student_busy_slots(student, semester, school_year)
            if all(not slots_overlap(cohort_slot.time_slot, t) for t in busy):
                StudentSchedule.objects.create(
                    student=student,
                    subject=section.subject,
                    section=section,
                    time_slot=cohort_slot.time_slot,
                    semester=semester,
                    school_year=school_year,
                )
                results.append({'subject': section.subject, 'time_slot': cohort_slot.time_slot})
                continue

        slot = schedule_section(section, semester, school_year)
        results.append({'subject': section.subject, 'time_slot': slot})

    # Subjects the student is enrolled in but has no section for.
    sectioned_subject_ids = {s.subject_id for s in student.sections.all()}
    subjects = [s for s in student.enrolled_subjects.all()
                if s.id not in sectioned_subject_ids]

    for subject in subjects:
        cohort_slot = (
            StudentSchedule.objects.filter(
                subject=subject,
                section__isnull=True,
                semester=semester,
                school_year=school_year,
            )
            .exclude(student=student)
            .exclude(time_slot__isnull=True)
            .select_related('time_slot')
            .first()
        )

        if cohort_slot is not None:
            busy = get_student_busy_slots(student, semester, school_year)
            if all(not slots_overlap(cohort_slot.time_slot, taken) for taken in busy):
                StudentSchedule.objects.create(
                    student=student,
                    subject=subject,
                    time_slot=cohort_slot.time_slot,
                    semester=semester,
                    school_year=school_year,
                )
                results.append({'subject': subject, 'time_slot': cohort_slot.time_slot})
                continue

        slot = schedule_subject(subject, semester, school_year)
        results.append({'subject': subject, 'time_slot': slot})

    return results


def regenerate_all_schedules(semester='', school_year='', student_ids=None):
    """
    Rebuild every class for a term.

    Sections that have students are scheduled first, each at one time shared by
    its own roster. Subjects that still have enrolled students but no sections
    are then scheduled as a whole, so pre-section data keeps working.

    `student_ids` limits which students' enrollments are considered, but any
    section or subject they share is still moved as a whole to keep the roster
    on one time.
    """
    from students.models import Student
    from subjects.models import Subject

    from .models import Section

    students = Student.objects.all()
    if student_ids:
        students = students.filter(id__in=student_ids)
    student_id_list = list(students.values_list('id', flat=True))

    StudentSchedule.objects.filter(
        semester=semester, school_year=school_year
    ).delete()

    results = []

    sections = list(
        Section.objects.filter(students__id__in=student_id_list)
        .distinct()
        .order_by('subject__code', 'code')
    )
    section_subject_ids = {s.subject_id for s in sections}

    for section in sections:
        slot = schedule_section(section, semester, school_year)
        results.append({
            'subject': section.subject,
            'section': section.code,
            'time_slot': slot,
            'student_count': len(section_students(section)),
        })

    # Subjects not yet divided into sections still need a class time.
    subjects = [
        s for s in Subject.objects.filter(
            enrolled_students__id__in=student_id_list
        ).distinct().order_by('code')
        if s.id not in section_subject_ids
    ]
    for subject in subjects:
        slot = schedule_subject(subject, semester, school_year)
        results.append({
            'subject': subject,
            'section': None,
            'time_slot': slot,
            'student_count': len(subject_students(subject)),
        })

    return results
