import { useState } from 'react'
import Modal from '../Modal'

export default function SectionRosterModal({
  isOpen,
  onClose,
  subject,
  enrolledStudents,
  allStudents,
  selectedStudentIds,
  onToggleStudent,
  onEnrollmentChange,
  savingEnrollment,
  isAdmin,
}) {
  const [studentSearch, setStudentSearch] = useState('')

  if (!isOpen || !subject) return null

  const enrolledIdSet = new Set(enrolledStudents.map((s) => s.id))
  const alreadyEnrolled = (id) => enrolledIdSet.has(id)
  const searchTerm = studentSearch.trim().toLowerCase()
  const candidates = allStudents.filter((s) => {
    if (!searchTerm) return true
    return (
      s.name.toLowerCase().includes(searchTerm) ||
      String(s.id).toLowerCase().includes(searchTerm) ||
      (s.program || '').toLowerCase().includes(searchTerm)
    )
  })

  return (
    <Modal
      title={`Students in ${subject.code}`}
      onClose={onClose}
      onCancel={onClose}
      onSave={() => onEnrollmentChange(selectedStudentIds, false)}
      saving={savingEnrollment}
      saveDisabled={selectedStudentIds.length === 0}
      footer={
        <button
          className="btn btn-danger"
          onClick={() => onEnrollmentChange(selectedStudentIds, true)}
          disabled={savingEnrollment || selectedStudentIds.length === 0}
          type="button"
        >
          {savingEnrollment ? <span className="spinner" /> : 'Remove selected'}
        </button>
      }
    >
      <div className="form-group">
        <label className="form-label" htmlFor="student-search">
          Add students to {subject.code}
        </label>
        <input
          id="student-search"
          className="form-input"
          type="text"
          placeholder="Search by name, ID, or program..."
          value={studentSearch}
          onChange={(e) => setStudentSearch(e.target.value)}
        />
        <p className="form-hint">
          Tick any number of students, then choose Enroll or Remove. Everyone in this
          subject shares one class time.
        </p>
      </div>

      <div className="student-picker" id="subject-student-picker">
        {candidates.length === 0 ? (
          <div className="table-empty">No students match.</div>
        ) : (
          candidates.map((s) => (
            <label key={s.id} className="student-picker-row">
              <input
                type="checkbox"
                checked={selectedStudentIds.includes(s.id)}
                onChange={() => onToggleStudent(s.id)}
              />
              <span>
                <span style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>{s.name}</span>
                <span style={{ color: 'var(--color-gray-500)' }}>
                  {' '}
                  &middot; {s.id} &middot; {s.program}
                </span>
              </span>
              {alreadyEnrolled(s.id) && <span className="badge badge-student">Enrolled</span>}
            </label>
          ))
        )}
      </div>

      <div className="form-group" style={{ marginTop: 'var(--space-5)' }}>
        <label className="form-label">
          Currently enrolled ({enrolledStudents.length})
        </label>
        {enrolledStudents.length === 0 ? (
          <div style={{ color: 'var(--color-gray-500)', fontSize: 'var(--font-sm)' }}>
            No students enrolled yet.
          </div>
        ) : (
          <div className="chip-list">
            {enrolledStudents.map((s) => (
              <span key={s.id} className="chip">
                {s.name}
                {isAdmin && (
                  <button
                    type="button"
                    className="chip-remove"
                    title={`Remove ${s.name}`}
                    onClick={() => onEnrollmentChange([s.id], true)}
                  >
                    &times;
                  </button>
                )}
              </span>
            ))}
          </div>
        )}
      </div>
    </Modal>
  )
}
