import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'
import { IconChevronLeft, IconPlus, IconEdit } from '../components/Icons'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { gradeBadgeClass, gpaColor, gwaColor } from '../utils/grades'
import TermFields from '../components/TermFields'
import useTerms from '../hooks/useTerms'

export default function StudentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAdmin } = useAuth()
  const { addToast } = useToast()
  const { current } = useTerms()

  const [data, setData] = useState(null)
  const [enrolledSubjects, setEnrolledSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  // Enrollment modal state
  const [showEnrollModal, setShowEnrollModal] = useState(false)
  const [allSubjects, setAllSubjects] = useState([])
  const [selectedSubjectIds, setSelectedSubjectIds] = useState([])
  const [savingEnrollment, setSavingEnrollment] = useState(false)
  const [enrollTerm, setEnrollTerm] = useState(current)
  const [loadingSubjects, setLoadingSubjects] = useState(false)

  useEffect(() => {
    fetchStudentData()
  }, [id])

  const fetchStudentData = async () => {
    setLoading(true)
    try {
      const [gradesRes, enrolledRes] = await Promise.all([
        api.get(`/students/${id}/grades/`),
        api.get(`/students/${id}/enrolled/`),
      ])
      setData(gradesRes.data)
      setEnrolledSubjects(enrolledRes.data.enrolled_subjects || [])
    } catch (err) {
      console.error('Student detail fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openEnrollModal = async () => {
    setSelectedSubjectIds(enrolledSubjects.map((s) => s.id))
    setShowEnrollModal(true)
    if (allSubjects.length === 0) {
      setLoadingSubjects(true)
      try {
        const res = await api.get('/subjects/', { params: { page_size: 100 } })
        setAllSubjects(res.data.results || res.data)
      } catch (err) {
        console.error('Subjects fetch error:', err)
        addToast('Failed to load subjects', 'error')
      } finally {
        setLoadingSubjects(false)
      }
    }
  }

  const toggleSubject = (subId) => {
    setSelectedSubjectIds((prev) =>
      prev.includes(subId) ? prev.filter((i) => i !== subId) : [...prev, subId]
    )
  }

  const handleSaveEnrollment = async () => {
    setSavingEnrollment(true)
    try {
      const res = await api.post(`/students/${id}/enroll/`, {
        subject_ids: selectedSubjectIds,
        semester: enrollTerm.semester,
        school_year: enrollTerm.school_year,
      })
      const scheduled = res.data?.scheduled_count
      addToast(
        scheduled === undefined
          ? 'Enrollment updated successfully'
          : `Enrollment updated — ${scheduled} class${scheduled === 1 ? '' : 'es'} scheduled`,
        'success'
      )
      setShowEnrollModal(false)
      const enrolledRes = await api.get(`/students/${id}/enrolled/`)
      setEnrolledSubjects(enrolledRes.data.enrolled_subjects || [])
    } catch (err) {
      console.error('Enrollment save error:', err)
      const msg = err.response?.data?.detail || 'Failed to update enrollment.'
      addToast(msg, 'error')
    } finally {
      setSavingEnrollment(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-page">
        <div className="spinner spinner-lg" />
      </div>
    )
  }

  if (!data) {
    return <div className="loading-page">Student not found.</div>
  }

  const totalEnrolledUnits = enrolledSubjects.reduce((sum, s) => sum + (s.units || 0), 0)

  return (
    <div>
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => navigate('/students')}
        style={{ marginBottom: 'var(--space-4)' }}
      >
        <IconChevronLeft /> Back to Students
      </button>

      <div className="detail-header">
        <div className="detail-header-info">
          <h2>{data.student_name}</h2>
          <p>{data.student_id} &middot; {data.email}</p>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-field">
          <div className="detail-field-label">Program</div>
          <div className="detail-field-value">{data.program}</div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">Year Level</div>
          <div className="detail-field-value">{data.year_level}</div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">General Weighted Average</div>
          <div className="detail-field-value" style={{ color: gwaColor(data.gwa) }}>
            {(data.gwa ?? 5).toFixed(2)}
          </div>
          <div className="detail-field-hint">Grade points weighted by units</div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">GPA (simple average)</div>
          <div className="detail-field-value" style={{ color: gpaColor(data.gpa) }}>
            {data.gpa.toFixed(2)}
          </div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">Units Earned</div>
          <div className="detail-field-value">{data.units_earned ?? 0}</div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">Total Grades</div>
          <div className="detail-field-value">{data.total_grades}</div>
        </div>
      </div>

      {/* Enrolled Subjects Section */}
      <div className="table-container" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="table-toolbar" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--font-base)', fontWeight: 600, color: 'var(--color-gray-800)' }}>
              Enrolled Subjects ({enrolledSubjects.length})
            </h3>
            <span style={{
              fontSize: 'var(--font-xs)',
              background: 'var(--color-gray-100)',
              color: 'var(--color-gray-700)',
              padding: '2px 8px',
              borderRadius: '9999px',
              fontWeight: 500
            }}>
              {totalEnrolledUnits} total units
            </span>
          </div>
          {isAdmin && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={openEnrollModal}
              id="manage-enrollment-btn"
            >
              <IconEdit /> Manage Enrollment
            </button>
          )}
        </div>

        {enrolledSubjects.length === 0 ? (
          <div className="table-empty">
            No subjects currently enrolled.
            {isAdmin && (
              <div style={{ marginTop: 'var(--space-2)' }}>
                <button className="btn btn-primary btn-sm" onClick={openEnrollModal}>
                  <IconPlus /> Enroll Subjects
                </button>
              </div>
            )}
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject Code</th>
                <th>Subject Name</th>
                <th>Units</th>
                <th>Instructor</th>
              </tr>
            </thead>
            <tbody>
              {enrolledSubjects.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600, color: 'var(--color-gray-900)' }}>{s.code}</td>
                  <td>{s.name}</td>
                  <td>{s.units}</td>
                  <td style={{ color: 'var(--color-gray-600)' }}>{s.instructor_name || 'Unassigned'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Grade Records Section */}
      <div className="table-container">
        <div className="table-toolbar">
          <h3 style={{ fontSize: 'var(--font-base)', fontWeight: 600, color: 'var(--color-gray-800)' }}>
            Grade Records
          </h3>
        </div>

        {data.grades.length === 0 ? (
          <div className="table-empty">No grades recorded yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject Code</th>
                <th>Subject</th>
                <th>Units</th>
                <th>Score</th>
                <th>Grade</th>
                <th>Points</th>
                <th>Recorded By</th>
              </tr>
            </thead>
            <tbody>
              {data.grades.map((g) => (
                <tr key={g.id}>
                  <td style={{ fontWeight: 500 }}>{g.subject.code}</td>
                  <td>{g.subject.name}</td>
                  <td>{g.subject.units}</td>
                  <td>{g.score}</td>
                  <td><span className={gradeBadgeClass(g.letter)}>{g.letter}</span></td>
                  <td>{g.grade_points}</td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{g.recorded_by || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Enroll Subjects Modal */}
      {showEnrollModal && (
        <Modal
          title={`Manage Enrollment — ${data.student_name}`}
          onClose={() => setShowEnrollModal(false)}
          footer={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
              <span style={{ fontSize: 'var(--font-sm)', color: 'var(--color-gray-600)' }}>
                <strong>{selectedSubjectIds.length}</strong> selected (
                {allSubjects
                  .filter((s) => selectedSubjectIds.includes(s.id))
                  .reduce((sum, s) => sum + (s.units || 0), 0)}{' '}
                units)
              </span>
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowEnrollModal(false)}
                  disabled={savingEnrollment}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleSaveEnrollment}
                  disabled={savingEnrollment}
                >
                  {savingEnrollment ? 'Saving...' : 'Save Enrollment'}
                </button>
              </div>
            </div>
          }
        >
          <div>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--color-gray-600)', marginBottom: 'var(--space-3)' }}>
              Tick every subject this student is taking. You can select as many as you
              like.
            </p>

            <div className="form-row" style={{ marginBottom: 'var(--space-4)' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <TermFields
                  idPrefix="enroll"
                  semester={enrollTerm.semester}
                  schoolYear={enrollTerm.school_year}
                  onChange={({ semester, schoolYear }) =>
                    setEnrollTerm({ semester, school_year: schoolYear })
                  }
                />
              </div>
            </div>

            {selectedSubjectIds.length > 0 && (
              <div className="alert alert-info" style={{ marginBottom: 'var(--space-3)' }}>
                {selectedSubjectIds.length} subject{selectedSubjectIds.length !== 1 ? 's' : ''} selected
                — saves as this student's subjects for {enrollTerm.semester} {enrollTerm.school_year}.
              </div>
            )}

            {loadingSubjects ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-4)' }}>
                <div className="spinner" />
              </div>
            ) : (
              <div className="subject-chips">
                {allSubjects.map((s) => {
                  const isSelected = selectedSubjectIds.includes(s.id)
                  return (
                    <button
                      type="button"
                      key={s.id}
                      className={`subject-chip${isSelected ? ' selected' : ''}`}
                      onClick={() => toggleSubject(s.id)}
                    >
                      <span>{isSelected ? '✓' : '+'}</span>
                      <span><strong>{s.code}</strong> &middot; {s.name} ({s.units}u)</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
