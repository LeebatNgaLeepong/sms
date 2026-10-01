import Modal from '../Modal'
import TermFields from '../TermFields'

export default function ScheduleEntryModal({
  isOpen,
  onClose,
  editSchedule,
  scheduleForm,
  setScheduleForm,
  onSave,
  savingSchedule,
  students,
  subjects,
  subjectSections,
  timeSlots,
  DAYS,
  formatTime,
  SLOT_TYPE_LABELS,
}) {
  if (!isOpen) return null

  return (
    <Modal
      title={editSchedule ? 'Edit Schedule Entry' : 'Add Schedule Entry'}
      onClose={onClose}
      onCancel={onClose}
      onSave={onSave}
      saving={savingSchedule}
    >
      <form id="schedule-form" onSubmit={onSave}>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="schedule-student">Student</label>
            <select
              id="schedule-student"
              className="form-select"
              value={scheduleForm.student}
              onChange={(e) => setScheduleForm({ ...scheduleForm, student: e.target.value })}
              required
            >
              <option value="">Select student</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="schedule-subject">Subject</label>
            <select
              id="schedule-subject"
              className="form-select"
              value={scheduleForm.subject}
              onChange={(e) =>
                setScheduleForm({ ...scheduleForm, subject: e.target.value, section: '' })
              }
              required
            >
              <option value="">Select subject</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.code} &middot; {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {subjectSections.length > 0 && (
          <div className="form-group">
            <label className="form-label" htmlFor="schedule-section">Section (optional)</label>
            <select
              id="schedule-section"
              className="form-select"
              value={scheduleForm.section}
              onChange={(e) => setScheduleForm({ ...scheduleForm, section: e.target.value })}
            >
              <option value="">No section</option>
              {subjectSections.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.subject_code}-{s.code} · {s.enrolled_count}/{s.capacity}
                </option>
              ))}
            </select>
            <p className="form-hint">
              If the student already has this subject this term, saving moves the class to
              the time you pick.
            </p>
          </div>
        )}
        <TermFields
          idPrefix="schedule"
          semester={scheduleForm.semester}
          schoolYear={scheduleForm.school_year}
          onChange={({ semester, schoolYear }) =>
            setScheduleForm((f) => ({ ...f, semester, school_year: schoolYear }))
          }
        />
        <div className="form-group">
          <label className="form-label" htmlFor="schedule-slot">Time Slot</label>
          <select
            id="schedule-slot"
            className="form-select"
            value={scheduleForm.time_slot}
            onChange={(e) => setScheduleForm({ ...scheduleForm, time_slot: e.target.value })}
            required
          >
            <option value="">Select time slot</option>
            {timeSlots.map((slot) => (
              <option key={slot.id} value={slot.id}>
                {DAYS.find((d) => d.value === slot.day)?.full} {formatTime(slot.start_time)}
                {' – '}
                {formatTime(slot.end_time)} &middot; {SLOT_TYPE_LABELS[slot.slot_type]}
              </option>
            ))}
          </select>
        </div>
      </form>
    </Modal>
  )
}
