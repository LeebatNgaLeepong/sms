import { useState, useEffect } from 'react'
import api from '../api'
import { useToast } from '../context/ToastContext'
import Modal from './Modal'
import TermFields from './TermFields'
import useTerms from '../hooks/useTerms'
import { gradeBadgeClass } from '../utils/grades'

/** Compare "HH:MM" strings; true when end is not after start. */
const isEndBeforeStart = (start, end) => {
  if (!start || !end) return false
  return end <= start
}

/**
 * The record/edit grade form, shared by the Grades page and the student page
 * so a teacher can change a grade from either place.
 */
export default function GradeFormModal({ show, grade, studentId, studentName, onClose, onSaved }) {
  const { addToast } = useToast()
  const { current } = useTerms()
  const [subjects, setSubjects] = useState([])
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    student: studentId || '',
    subject: '',
    score: '',
    is_incomplete: false,
    manual_points: '',
    remark: '',
  })

  useEffect(() => {
    if (!show) return
    api
      .get('/subjects/', { params: { page_size: 300 } })
      .then((res) => setSubjects(res.data.results || res.data || []))
      .catch((err) => console.error('Subjects fetch error:', err))
  }, [show])

  // Seed the form each time the modal opens.
  useEffect(() => {
    if (!show) return
    if (grade) {
      setForm({
        student: studentId || '',
        subject: grade.subject?.id ?? grade.subject ?? '',
        score: grade.score ?? '',
        is_incomplete: Boolean(grade.is_incomplete),
        manual_points: grade.manual_points ?? '',
        remark: grade.remark ?? '',
      })
    } else {
      setForm({
        student: studentId || '',
        subject: '',
        score: '',
        is_incomplete: false,
        manual_points: '',
        remark: '',
      })
    }
  }, [show, grade, studentId])

  const endTimeInvalid = isEndBeforeStart(form.start_time, form.end_time)

  const preview = form.is_incomplete
    ? { letter: 'INC', points: 0 }
    : form.manual_points
      ? {
          letter: Number(form.manual_points).toFixed(2),
          points: Number(form.manual_points),
          label: 'Manual entry',
        }
      : bandForScoreLocal(form.score)

  const handleSave = async (e) => {
    e?.preventDefault()
    setSaving(true)
    const payload = {
      student: form.student,
      subject: parseInt(form.subject, 10),
      score: form.is_incomplete ? null : form.score === '' ? null : form.score,
      is_incomplete: form.is_incomplete,
      manual_points:
        form.is_incomplete || !form.manual_points ? null : form.manual_points,
      remark: form.remark || '',
    }
    try {
      if (grade) {
        await api.put(`/grades/${grade.id}/`, payload)
        addToast(
          form.is_incomplete ? 'Marked as INC' : 'Grade updated successfully',
          'success'
        )
      } else {
        await api.post('/grades/', payload)
        addToast(
          form.is_incomplete ? 'Recorded as INC' : 'Grade recorded successfully',
          'success'
        )
      }
      onSaved?.()
      onClose()
    } catch (err) {
      const data = err.response?.data
      let msg = 'Could not save the grade'
      if (typeof data === 'string') msg = data
      else if (data && typeof data === 'object') {
        msg = Object.entries(data)
          .map(([k, v]) => (k === 'detail' ? v : `${k}: ${Array.isArray(v) ? v.join(', ') : v}`))
          .join('. ')
      }
      addToast(msg, 'error')
    } finally {
      setSaving(false)
    }
  }

  // All hooks above must run every render, so the guard sits here rather than at
  // the top. Without it the dialog never goes away and Cancel appears inert.
  if (!show) return null

  return (
    <Modal
      title={grade ? `Edit Grade${studentName ? ` · ${studentName}` : ''}` : 'Record Grade'}
      onClose={onClose}
      onCancel={onClose}
      onSave={handleSave}
      saving={saving}
    >
      <form id="grade-form" onSubmit={handleSave}>
        {!grade && (
          <div className="form-group">
            <label className="form-label" htmlFor="grade-student">
              Student
            </label>
            <input
              id="grade-student"
              className="form-input"
              value={studentId || form.student}
              disabled
              placeholder="Select a student from their page"
            />
            <p className="form-hint">
              Open a student's page to record a grade for them.
            </p>
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="grade-subject">
            Subject
          </label>
          <select
            id="grade-subject"
            className="form-select"
            value={form.subject}
            onChange={(e) => setForm({ ...form, subject: e.target.value })}
            required
            disabled={!!grade}
          >
            <option value="">Choose subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} · {s.name} ({s.units} units)
              </option>
            ))}
          </select>
          {grade && (
            <p className="form-hint">
              The subject cannot be changed. Delete the grade and record it again to
              move it.
            </p>
          )}
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="grade-score">
            Score (0 - 100)
          </label>
          <input
            id="grade-score"
            className="form-input"
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={form.score}
            onChange={(e) => setForm({ ...form, score: e.target.value })}
            disabled={form.is_incomplete || !!form.manual_points}
            required={!form.is_incomplete && !form.manual_points}
            placeholder={
              form.is_incomplete
                ? 'Not applicable for INC'
                : form.manual_points
                  ? 'Not used when a grade is chosen'
                  : 'e.g., 85.50'
            }
          />
          {preview && !endTimeInvalid && (
            <div className="grade-preview" id="grade-preview">
              <span className="grade-preview-label">Records as</span>
              <span className={`badge ${gradeBadgeClass(preview.letter)}`}>
                {preview.letter}
              </span>
              <span className="grade-preview-points">
                {Number(preview.points ?? 0).toFixed(2)}
              </span>
              {preview.label && (
                <span className="grade-preview-label-text">{preview.label}</span>
              )}
            </div>
          )}
          <label className="checkbox-row" htmlFor="grade-incomplete">
            <input
              id="grade-incomplete"
              type="checkbox"
              checked={form.is_incomplete}
              onChange={(e) =>
                setForm({
                  ...form,
                  is_incomplete: e.target.checked,
                  score: e.target.checked ? '' : form.score,
                  manual_points: e.target.checked ? '' : form.manual_points,
                })
              }
            />
            <span>
              Mark as <strong>INC</strong> (incomplete)
            </span>
          </label>
          <p className="form-hint">
            INC means the subject is not finished. It has no grade points and is left
            out of GPA and GWA.
          </p>
        </div>

        {!form.is_incomplete && (
          <div className="form-group">
            <label className="form-label" htmlFor="grade-manual">
              Or choose the grade directly
            </label>
            <select
              id="grade-manual"
              className="form-select"
              value={form.manual_points}
              onChange={(e) =>
                setForm({
                  ...form,
                  manual_points: e.target.value,
                  score: e.target.value ? '' : form.score,
                })
              }
            >
              <option value="">Use the score bands above</option>
              {GRADE_OPTIONS.map((b) => (
                <option key={b.letter} value={b.points}>
                  {b.letter} — {b.label} ({b.description})
                </option>
              ))}
              <option value="4.00">4.00 — Manual entry (no band)</option>
            </select>
            <p className="form-hint">
              Setting a grade here overrides the score bands, which is how you record a
              grade the scale has no band for, such as 4.00.
            </p>
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="grade-remark">
            Remark (optional)
          </label>
          <input
            id="grade-remark"
            className="form-input"
            maxLength={255}
            value={form.remark}
            onChange={(e) => setForm({ ...form, remark: e.target.value })}
            placeholder="e.g. Retake passed, approved by dean"
          />
        </div>
      </form>
    </Modal>
  )
}

// Kept local so the modal renders instantly without waiting on a fetch.
const GRADE_OPTIONS = [
  { min: 98, letter: '1.00', points: 1.0, label: 'Outstanding', description: '98-100' },
  { min: 95, letter: '1.25', points: 1.25, label: 'Excellent', description: '95-97' },
  { min: 92, letter: '1.50', points: 1.5, label: 'Very Good', description: '92-94' },
  { min: 89, letter: '1.75', points: 1.75, label: 'Good', description: '89-91' },
  { min: 86, letter: '2.00', points: 2.0, label: 'Fairly Good', description: '86-88' },
  { min: 83, letter: '2.25', points: 2.25, label: 'Fair', description: '83-85' },
  { min: 80, letter: '2.50', points: 2.5, label: 'Satisfactory', description: '80-82' },
  { min: 77, letter: '2.75', points: 2.75, label: 'Needs Improvement', description: '77-79' },
  { min: 75, letter: '3.00', points: 3.0, label: 'Passing', description: '75-76' },
  { min: 0, letter: '5.00', points: 5.0, label: 'Failed', description: 'Below 75' },
]

function bandForScoreLocal(score) {
  if (score === '' || score === null || score === undefined) return null
  const value = Number(score)
  if (Number.isNaN(value)) return null
  return GRADE_OPTIONS.find((b) => value >= b.min) || null
}