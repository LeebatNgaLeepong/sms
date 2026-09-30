import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconEdit, IconTrash } from '../components/Icons'
import { gradeBadgeClass, gradeDescription } from '../utils/grades'

export default function GradesPage() {
  const [grades, setGrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editGrade, setEditGrade] = useState(null)
  const [form, setForm] = useState({ student: '', subject: '', score: '' })
  const [saving, setSaving] = useState(false)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const [students, setStudents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])

  const [filterSubject, setFilterSubject] = useState('')
  const [filterTeacher, setFilterTeacher] = useState('')
  const [filterYear, setFilterYear] = useState('')

  const { isAdmin, isTeacher, isStudent } = useAuth()
  const { addToast } = useToast()

  const canModify = isAdmin || isTeacher

  useEffect(() => {
    fetchGrades()
  }, [page, filterSubject, filterTeacher, filterYear])

  useEffect(() => {
    fetchDropdownData()
  }, [])

  const fetchGrades = async () => {
    setLoading(true)
    try {
      const params = { page }
      if (search) params.student = search
      if (filterSubject) params.subject = filterSubject
      if (filterTeacher) params.teacher = filterTeacher
      if (filterYear) params.year_level = filterYear
      const res = await api.get('/grades/', { params })
      setGrades(res.data.results || res.data)
      setTotalCount(res.data.count || 0)
    } catch (err) {
      console.error('Grades fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchDropdownData = async () => {
    try {
      const [studentsRes, subjectsRes, teachersRes] = await Promise.all([
        api.get('/students/', { params: { page_size: 100 } }),
        api.get('/subjects/', { params: { page_size: 100 } }),
        api.get('/teachers/'),
      ])
      setStudents(studentsRes.data.results || studentsRes.data)
      setSubjects(subjectsRes.data.results || subjectsRes.data)
      setTeachers(teachersRes.data)
    } catch (err) {
      console.error('Dropdown data fetch error:', err)
    }
  }

  const clearFilters = () => {
    setSearch('')
    setFilterSubject('')
    setFilterTeacher('')
    setFilterYear('')
    setPage(1)
  }

  const openCreate = () => {
    setEditGrade(null)
    setForm({ student: '', subject: '', score: '' })
    setShowModal(true)
  }

  const openEdit = (grade) => {
    setEditGrade(grade)
    setForm({
      student: grade.student,
      subject: grade.subject,
      score: grade.score,
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
        score: form.score,
      }
      if (editGrade) {
        await api.put(`/grades/${editGrade.id}/`, payload)
        addToast('Grade updated successfully', 'success')
      } else {
        await api.post('/grades/', payload)
        addToast('Grade recorded successfully', 'success')
      }
      setShowModal(false)
      fetchGrades()
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
      fetchGrades()
    } catch {
      addToast('Failed to delete grade', 'error')
    }
  }

  const handleSearch = () => {
    setPage(1)
    fetchGrades()
  }

  const totalPages = Math.ceil(totalCount / 10)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Grades
          </h1>
          <p className="page-subtitle">
            {totalCount} grade record{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
        {canModify && (
          <button className="btn btn-primary" onClick={openCreate} id="add-grade-btn">
            <IconPlus /> Record Grade
          </button>
        )}
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Filter by student ID (e.g., STU-10001)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              id="grade-search"
            />
          </div>
          <button className="btn btn-secondary btn-sm" onClick={handleSearch}>
            Filter
          </button>
        </div>

        <div className="filter-row">
          <span className="filter-label">Filter By:</span>
          <select
            className="filter-select"
            value={filterSubject}
            onChange={(e) => { setFilterSubject(e.target.value); setPage(1); }}
            aria-label="Filter by Subject"
          >
            <option value="">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} - {s.name}
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filterTeacher}
            onChange={(e) => { setFilterTeacher(e.target.value); setPage(1); }}
            aria-label="Filter by Teacher"
          >
            <option value="">All Teachers</option>
            {teachers.map((t) => (
              <option key={t.id} value={t.id}>
                {t.first_name ? `${t.first_name} ${t.last_name}` : t.username}
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filterYear}
            onChange={(e) => { setFilterYear(e.target.value); setPage(1); }}
            aria-label="Filter by Year Level"
          >
            <option value="">All Year Levels</option>
            <option value="1st Year">1st Year</option>
            <option value="2nd Year">2nd Year</option>
            <option value="3rd Year">3rd Year</option>
            <option value="4th Year">4th Year</option>
          </select>

          {(search || filterSubject || filterTeacher || filterYear) && (
            <button className="btn btn-ghost btn-sm" onClick={clearFilters}>
              Reset Filters
            </button>
          )}
        </div>

        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : grades.length === 0 ? (
          <div className="table-empty">No grades found.</div>
        ) : (
          <table className="data-table" id="grades-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Subject</th>
                <th>Score</th>
                <th>Grade</th>
                <th>Points</th>
                <th>Recorded By</th>
                {canModify && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {grades.map((g) => (
                <tr key={g.id}>
                  <td>
                    <div>
                      <div style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>{g.student_name}</div>
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>{g.student}</div>
                    </div>
                  </td>
                  <td>
                    <div>
                      <div style={{ fontWeight: 500 }}>{g.subject_code}</div>
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>{g.subject_name}</div>
                    </div>
                  </td>
                  <td>{g.score}</td>
                  <td><span className={gradeBadgeClass(g.letter)} title={gradeDescription(g.letter)}>{g.letter}</span></td>
                  <td>{g.grade_points}</td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{g.recorded_by_username || '—'}</td>
                  {canModify && (
                    <td>
                      <div className="table-actions">
                        <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEdit(g)}>
                          <IconEdit />
                        </button>
                        <button className="btn-icon btn-ghost" title="Delete" onClick={() => handleDelete(g)}>
                          <IconTrash />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <div className="table-pagination">
            <span>Page {page} of {totalPages}</span>
            <div className="table-pagination-buttons">
              <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <button className="btn btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <Modal
          title={editGrade ? 'Edit Grade' : 'Record Grade'}
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
              <label className="form-label" htmlFor="grade-student">Student</label>
              <select
                id="grade-student"
                className="form-select"
                value={form.student}
                onChange={(e) => setForm({ ...form, student: e.target.value })}
                required
                disabled={!!editGrade}
              >
                <option value="">Select student</option>
                {students.map((s) => (
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
              <label className="form-label" htmlFor="grade-score">Score (0 - 100)</label>
              <input
                id="grade-score"
                className="form-input"
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={form.score}
                onChange={(e) => setForm({ ...form, score: e.target.value })}
                required
                placeholder="e.g., 85.50"
              />
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
