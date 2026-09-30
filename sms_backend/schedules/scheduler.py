"""
Schedule generation utilities.
Provides automatic conflict-free class schedule generation for students.
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

    grouped = {day: sorted((s for s in slots if s.day == day), key=lambda s: s.start_time) for day in days}
    ordered = []
    for step in range(len(days)):
        ordered.extend(grouped[days[(start_offset + step) % len(days)]])
    return ordered


def get_available_slots(student, semester=None, school_year=None):
    """
    Return all time slots that are NOT currently occupied by the student's
    existing schedules (for the given semester/year).
    """
    qs = TimeSlot.objects.all()
    existing = StudentSchedule.objects.filter(
        student=student,
        semester=semester,
        school_year=school_year,
    ).values_list('time_slot_id', flat=True)
    if existing:
        qs = qs.exclude(id__in=list(existing))
    return qs


def slots_overlap(slot_a, slot_b):
    """
    Return True if two time slots overlap in time on the same day.
    """
    if slot_a.day != slot_b.day:
        return False
    a_start = slot_a.start_time
    a_end = slot_a.end_time
    b_start = slot_b.start_time
    b_end = slot_b.end_time
    # Overlap if one starts before the other ends
    return a_start < b_end and b_start < a_end


def get_student_busy_slots(student, semester=None, school_year=None):
    """
    Return the set of time slots that the student is already scheduled in.
    """
    busy = set()
    existing_schedules = StudentSchedule.objects.filter(
        student=student,
        semester=semester,
        school_year=school_year,
    ).select_related('time_slot')
    for sched in existing_schedules:
        busy.add(sched.time_slot)
    return busy


def generate_schedule_for_subjects(student, subject_ids, semester='', school_year=''):
    """
    Automatically assign non-conflicting time slots to a student's enrolled subjects.

    Strategy:
      1. Collect the student's currently busy slots (existing schedules).
      2. For each subject to schedule, find an available slot that does not
         conflict with any busy slot.
      3. If no non-conflicting slot exists, skip that subject (do not overwrite).
      4. Assign slots in a round-robin fashion across days to distribute load.

    Returns a list of dicts: [{'subject': subject, 'time_slot': slot or None, 'created': bool}]
    """
    from subjects.models import Subject

    subjects = list(Subject.objects.filter(id__in=subject_ids))
    busy_slots = get_student_busy_slots(student, semester=semester, school_year=school_year)

    # All available time slots in chronological order
    all_slots = sorted(TimeSlot.objects.all(), key=slot_sort_key)

    results = []

    # Track slots we assign in this run to avoid self-conflict
    newly_assigned = set()

    for subject_index, subject in enumerate(subjects):
        # Skip if already scheduled for this subject/semester/year
        existing = StudentSchedule.objects.filter(
            student=student,
            subject=subject,
            semester=semester,
            school_year=school_year,
        ).first()
        if existing:
            results.append({
                'subject': subject,
                'time_slot': existing.time_slot,
                'created': False,
            })
            continue

        # Find a slot that does not conflict with busy_slots or newly_assigned.
        # Start the search on a rotating day so a full week is used.
        assigned = None
        for slot in order_slots_by_preference(all_slots, start_offset=subject_index):
            # Check against existing busy slots
            conflict = False
            for busy in busy_slots:
                if slots_overlap(slot, busy):
                    conflict = True
                    break
            if conflict:
                continue
            # Check against newly assigned slots in this run
            for new_slot in newly_assigned:
                if slots_overlap(slot, new_slot):
                    conflict = True
                    break
            if conflict:
                continue
            assigned = slot
            break

        if assigned:
            schedule = StudentSchedule.objects.create(
                student=student,
                subject=subject,
                time_slot=assigned,
                semester=semester,
                school_year=school_year,
            )
            busy_slots.add(assigned)
            newly_assigned.add(assigned)
            results.append({
                'subject': subject,
                'time_slot': assigned,
                'created': True,
            })
        else:
            results.append({
                'subject': subject,
                'time_slot': None,
                'created': False,
            })

    return results


def regenerate_student_schedule(student, semester='', school_year=''):
    """
    Regenerate the entire schedule for a student by clearing existing schedules
    and re-assigning all enrolled subjects.
    """
    enrolled_subjects = list(student.enrolled_subjects.all())
    # Clear existing schedules
    StudentSchedule.objects.filter(
        student=student,
        semester=semester,
        school_year=school_year,
    ).delete()
    return generate_schedule_for_subjects(
        student,
        [s.id for s in enrolled_subjects],
        semester=semester,
        school_year=school_year,
    )