import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import StudentGradePanel from '../components/StudentGradePanel'
import { IconSearch, IconPlus } from '../components/Icons'
import { gwaColor, gradeBadgeClass } from '../utils/grades'
import useGradeScale from '../hooks/useGradeScale'

export default function GradesPage() {
  const [students, setStudents] = useState([])
  const [studentOptions, setStudentOptions] = useState([])
  const [studentGrades, setStudentGrades] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingGrades, setLoadingGrades] = useState(false)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editGrade, setEditGrade] = useState(null)
  const [form, setForm] = useState({
    student: '',
    subject: '',
    score: '',
    is_incomplete: false,
    manual_points: '',
    remark: '',
  })
  const [saving, setSaving] = useState(false)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const [subjects, setSubjects] = useState([])

  const { isAdmin, isTeacher, isStudent } = useAuth()
  const { addToast } = useToast()
  const { bands, bandForScore, bandForPoints } = useGradeScale()

  const canModify = isAdmin || isTeacher

  // Show what the server will record before it is saved.
  const preview = form.is_incomplete
    ? { letter: 'INC', points: 0, label: 'Not counted' }
    : form.manual_points
      ? bandForPoints(form.manual_points) || {
          letter: Number(form.manual_points).toFixed(2),
          points: form.manual_points,
          label: 'Manual entry',
        }
      : bandForScore(form.score)

  useEffect(() => {
    fetchStudents()
  }, [page, search])

  useEffect(() => {
    api
      .get('/subjects/', { params: { page_size: 200 } })
      .then((res) => setSubjects(res.data.results || res.data || []))
      .catch((err) => console.error('Subjects fetch error:', err))
  }, [])

  // The student picker needs the full list, not just the visible page.
  useEffect(() => {
    api
      .get('/students/', { params: { page_size: 500 } })
      .then((res) => setStudentOptions(res.data.results || res.data || []))
      .catch((err) => console.error('Student options fetch error:', err))
  }, [])

  const fetchStudents = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 10 }
      if (search) params.search = search
      const res = await api.get('/students/', { params })
      setStudents(res.data.results || res.data || [])
      setTotalCount(res.data.count || 0)
    } catch (err) {
      console.error('Students fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openStudent = useCallback(async (student) => {
    setLoadingGrades(true)
    setStudentGrades({ ...student, grades: [], total_grades: student.grades_count || 0 })
    try {
      const res = await api.get(`/students/${student.id}/grades/`)
      setStudentGrades(res.data)
    } catch (err) {
      console.error('Student grades fetch error:', err)
      addToast('Failed to load this student\'s grades', 'error')
      setStudentGrades(null)
    } finally {
      setLoadingGrades(false)
    }
  }, [addToast])

  const closeStudent = () => {
    setStudentGrades(null)
    fetchStudents()
  }

  const refreshStudentGrades = async () => {
    if (!studentGrades) return
    const res = await api.get(`/students/${studentGrades.student_id}/grades/`)
    setStudentGrades(res.data)
    fetchStudents()
  }

  const openCreate = (studentId = '') => {
    setEditGrade(null)
    setForm({
      student: studentId,
      subject: '',
      score: '',
      is_incomplete: false,
      manual_points: '',
      remark: '',
    })
    setShowModal(true)
  }

  const openEdit = (grade) => {
    setEditGrade(grade)
    setForm({
      student: grade.student_id || studentGrades?.student_id || '',
      subject: grade.subject?.id ?? '',
      score: grade.score ?? '',
      is_incomplete: Boolean(grade.is_incomplete),
      manual_points: grade.manual_points ?? '',
      remark: grade.remark ?? '',
    })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        student: form.student,
        subject: parseInt(form.subject),
        score: form.is_incomplete ? null : form.score === '' ? null : form.score,
        is_incomplete: form.is_incomplete,
        manual_points:
          form.is_incomplete || !form.manual_points ? null : form.manual_points,
        remark: form.remark || '',
      }
      if (editGrade) {
        await api.put(`/grades/${editGrade.id}/`, payload)
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
      setShowModal(false)
      if (studentGrades) {
        await refreshStudentGrades()
      } else {
        fetchStudents()
      }
    } catch (err) {
      const msg = err.response?.data
      let errorText = 'An error occurred'
      if (typeof msg === 'object') {
        errorText = Object.entries(msg)
          .map(([k, v]) => (Array.isArray(v) ? v.join(', ') : v))
          .join('. ')
      }
      addToast(errorText, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (grade) => {
    if (!window.confirm('Delete this grade record?')) return
    try {
      await api.delete(`/grades/${grade.id}/`)
      addToast('Grade deleted', 'success')
      if (studentGrades) {
        await refreshStudentGrades()
      } else {
        fetchStudents()
      }
    } catch {
      addToast('Failed to delete grade', 'error')
    }
  }

  const handleSearch = () => {
    setPage(1)
    fetchStudents()
  }

  const totalPages = Math.ceil(totalCount / 10)

return (
    <div>
      {studentGrades ? (
        <StudentGradePanel
          data={studentGrades}
          loading={loadingGrades}
          canModify={canModify}
          onBack={closeStudent}
          onAdd={() => openCreate(studentGrades.student_id)}
          onEdit={openEdit}
          onDelete={handleDelete}
        />
      ) : (
        <>
          <div className="page-header">
            <div>
              <h1 className="page-title">Grades</h1>
              <p className="page-subtitle">
                Pick a student to view and manage their grades
              </p>
            </div>
          </div>

          <div className="table-container">
            <div className="table-toolbar">
              <div className="table-search">
                <IconSearch />
                <input
                  type="text"
                  placeholder="Search students by name, ID or program..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  id="grade-search"
                />
              </div>
              <button className="btn btn-secondary btn-sm" onClick={handleSearch}>
                Search
              </button>
            </div>

            {loading ? (
              <div className="loading-page"><div className="spinner spinner-lg" /></div>
            ) : students.length === 0 ? (
              <div className="table-empty">No students found.</div>
            ) : (
              <table className="data-table data-table-clickable" id="grade-students-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Program</th>
                    <th>Year</th>
                    <th>Subjects Graded</th>
                    <th>GWA</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr
                      key={s.id}
                      className="row-clickable"
                      onClick={() => openStudent(s)}
                      id={`student-grades-${s.id}`}
                    >
                      <td>
                        <div style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>
                          {s.name}
                        </div>
                        <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>
                          {s.id}
                        </div>
                      </td>
                      <td style={{ color: 'var(--color-gray-600)' }}>{s.program || '—'}</td>
                      <td style={{ color: 'var(--color-gray-600)' }}>{s.year_level || '—'}</td>
                      <td>
                        {s.grades_count ?? 0}
                        {s.incomplete_count > 0 && (
                          <span className="badge badge-gp-inc" style={{ marginLeft: 6 }}>
                            {s.incomplete_count} INC
                          </span>
                        )}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, color: gwaColor(s.gwa ?? 5) }}>
                          {(s.gwa ?? 5).toFixed(2)}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', color: 'var(--color-gray-400)' }}>
                        View grades &rsaquo;
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {totalPages > 1 && (
              <div className="table-pagination">
                <span>Page {page} of {totalPages}</span>
                <div className="table-pagination-buttons">
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
      {showModal && (
        <Modal
          title={
            editGrade
              ? 'Edit Grade'
              : form.is_incomplete
                ? 'Mark as INC'
                : 'Record Grade'
          }
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} form="grade-form" type="submit">
                {saving ? <span className="spinner" /> : editGrade ? 'Update' : 'Save'}
              </button>
            </>
          }
        >
          <form id="grade-form" onSubmit={handleSave}>
            <div className="form-group">
              <label className="form-label" htmlFor="grade-student">
                Student
              </label>
              <select
                id="grade-student"
                className="form-select"
                value={form.student}
                onChange={(e) => setForm({ ...form, student: e.target.value })}
                required
                disabled={!!editGrade || !!studentGrades}
              >
                <option value="">Select student</option>
                {studentOptions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id} - {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="grade-subject">Subject</label>
              <select
                id="grade-subject"
                className="form-select"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                required
                disabled={!!editGrade}
              >
                <option value="">Select subject</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} - {s.name}
                  </option>
                ))}
              </select>
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
              {preview && (
                <div className="grade-preview" id="grade-preview">
                  <span className="grade-preview-label">Records as</span>
                  <span className={`badge ${gradeBadgeClass(preview.letter)}`}>{preview.letter}</span>
                  <span className="grade-preview-points">{Number(preview.points).toFixed(2)}</span>
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
                  {bands.map((b) => (
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
      )}
    </div>
  )
}