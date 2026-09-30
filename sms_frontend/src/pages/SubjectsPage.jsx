import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconEdit, IconTrash, IconStudents } from '../components/Icons'

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editSubject, setEditSubject] = useState(null)
  const [form, setForm] = useState({ code: '', name: '', units: 3, instructor: '' })
  const [saving, setSaving] = useState(false)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [teachers, setTeachers] = useState([])

  const [showEnrollModal, setShowEnrollModal] = useState(false)
  const [enrollSubject, setEnrollSubject] = useState(null)
  const [enrolledStudents, setEnrolledStudents] = useState([])
  const [allStudents, setAllStudents] = useState([])
  const [selectedStudentIds, setSelectedStudentIds] = useState([])
  const [enrolledCounts, setEnrolledCounts] = useState({})
  const [savingEnrollment, setSavingEnrollment] = useState(false)
  const [studentSearch, setStudentSearch] = useState('')
  const { isAdmin } = useAuth()
  const { addToast } = useToast()

  useEffect(() => {
    fetchSubjects()
  }, [page, search])

  useEffect(() => {
    fetchTeachers()
    fetchAllStudents()
  }, [])

  const fetchTeachers = async () => {
    try {
      const res = await api.get('/teachers/')
      setTeachers(res.data)
    } catch (err) {
      console.error('Teachers fetch error:', err)
    }
  }

  const fetchAllStudents = async () => {
    try {
      const res = await api.get('/students/', { params: { page_size: 500 } })
      setAllStudents(res.data.results || res.data || [])
    } catch (err) {
      console.error('Students fetch error:', err)
    }
  }

  const fetchSubjects = async () => {
    setLoading(true)
    try {
      const res = await api.get('/subjects/', {
        params: { page, search: search || undefined },
      })
      const list = res.data.results || res.data
      setSubjects(list)
      setTotalCount(res.data.count || 0)
      loadEnrolledCounts(list)
    } catch (err) {
      console.error('Subjects fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  // The list endpoint does not include enrollment counts, so fetch them per subject.
  const loadEnrolledCounts = async (list) => {
    if (!isAdmin) return
    const entries = await Promise.all(
      list.map(async (s) => {
        try {
          const res = await api.get(`/subjects/${s.id}/students/`)
          return [s.id, res.data.count]
        } catch {
          return [s.id, null]
        }
      })
    )
    setEnrolledCounts(Object.fromEntries(entries))
  }

  const openEnrollment = async (subject) => {
    setEnrollSubject(subject)
    setSelectedStudentIds([])
    setShowEnrollModal(true)
    try {
      const [enrolledRes] = await Promise.all([api.get(`/subjects/${subject.id}/students/`)])
      setEnrolledStudents(enrolledRes.data.students || [])
    } catch (err) {
      console.error('Enrolled students fetch error:', err)
      setEnrolledStudents([])
    }
  }

  const toggleStudent = (id) => {
    setSelectedStudentIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const handleEnrollmentChange = async (studentIds, remove) => {
    if (!enrollSubject || studentIds.length === 0) {
      addToast('Select at least one student', 'error')
      return
    }
    setSavingEnrollment(true)
    try {
      const res = await api.post(`/subjects/${enrollSubject.id}/enroll/`, {
        student_ids: studentIds,
        remove,
      })
      const notFound = res.data.not_found || []
      let msg = remove
        ? `Removed ${studentIds.length} student(s) from ${enrollSubject.code}.`
        : `Enrolled ${studentIds.length} student(s) in ${enrollSubject.code}.`
      if (notFound.length) msg += ` Not found: ${notFound.join(', ')}.`
      addToast(msg, notFound.length ? 'error' : 'success')

      const enrolledRes = await api.get(`/subjects/${enrollSubject.id}/students/`)
      setEnrolledStudents(enrolledRes.data.students || [])
      setEnrolledCounts((prev) => ({ ...prev, [enrollSubject.id]: enrolledRes.data.count }))
      setSelectedStudentIds([])
      fetchAllStudents()
    } catch (err) {
      const data = err.response?.data
      const text =
        data && typeof data === 'object'
          ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('. ')
          : 'Failed to update enrollment'
      addToast(text, 'error')
    } finally {
      setSavingEnrollment(false)
    }
  }

  const openCreate = () => {
    setEditSubject(null)
    setForm({ code: '', name: '', units: 3, instructor: '' })
    setShowModal(true)
  }

  const openEdit = (subject) => {
    setEditSubject(subject)
    setForm({
      code: subject.code,
      name: subject.name,
      units: subject.units,
      instructor: subject.instructor || '',
    })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        ...form,
        instructor: form.instructor || null,
      }
      if (editSubject) {
        await api.put(`/subjects/${editSubject.id}/`, payload)
        addToast('Subject updated successfully', 'success')
      } else {
        await api.post('/subjects/', payload)
        addToast('Subject created successfully', 'success')
      }
      setShowModal(false)
      fetchSubjects()
    } catch (err) {
      const msg = err.response?.data
      const errorText = typeof msg === 'object'
        ? Object.values(msg).flat().join(', ')
        : 'An error occurred'
      addToast(errorText, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (subject) => {
    if (!window.confirm(`Delete subject ${subject.code}?`)) return
    try {
      await api.delete(`/subjects/${subject.id}/`)
      addToast('Subject deleted', 'success')
      fetchSubjects()
    } catch {
      addToast('Failed to delete subject', 'error')
    }
  }

  const totalPages = Math.ceil(totalCount / 10)

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
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Subjects
          </h1>
          <p className="page-subtitle">
            {totalCount} subject{totalCount !== 1 ? 's' : ''} available
          </p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={openCreate} id="add-subject-btn">
            <IconPlus /> Add Subject
          </button>
        )}
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Search subjects..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              id="subject-search"
            />
          </div>
        </div>

        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : subjects.length === 0 ? (
          <div className="table-empty">No subjects found.</div>
        ) : (
          <table className="data-table" id="subjects-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Units</th>
                <th>Instructor</th>
                <th>Students</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {subjects.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>{s.code}</td>
                  <td>{s.name}</td>
                  <td>{s.units}</td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{s.instructor_name || '—'}</td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => openEnrollment(s)}
                      id={`manage-students-${s.code}`}
                    >
                      <IconStudents /> {enrolledCounts[s.id] ?? '—'}
                    </button>
                  </td>
                  {isAdmin && (
                    <td>
                      <div className="table-actions">
                        <button className="btn-icon btn-ghost" title="Manage students" onClick={() => openEnrollment(s)}>
                          <IconStudents />
                        </button>
                        <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEdit(s)}>
                          <IconEdit />
                        </button>
                        <button className="btn-icon btn-ghost" title="Delete" onClick={() => handleDelete(s)}>
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
          title={editSubject ? 'Edit Subject' : 'Add Subject'}
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} form="subject-form" type="submit">
                {saving ? <span className="spinner" /> : editSubject ? 'Update' : 'Create'}
              </button>
            </>
          }
        >
          <form id="subject-form" onSubmit={handleSave}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="subject-code">Course Code</label>
                <input
                  id="subject-code"
                  className="form-input"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  required
                  placeholder="e.g., CS101"
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="subject-units">Units</label>
                <input
                  id="subject-units"
                  className="form-input"
                  type="number"
                  min="1"
                  max="12"
                  value={form.units}
                  onChange={(e) => setForm({ ...form, units: parseInt(e.target.value) || 1 })}
                  required
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="subject-name">Subject Name</label>
              <input
                id="subject-name"
                className="form-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="e.g., Introduction to Programming"
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="subject-instructor">Assigned Instructor</label>
              <select
                id="subject-instructor"
                className="form-select"
                value={form.instructor || ''}
                onChange={(e) => setForm({ ...form, instructor: e.target.value ? parseInt(e.target.value) : '' })}
              >
                <option value="">No Instructor Assigned</option>
                {teachers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.first_name ? `${t.first_name} ${t.last_name}` : t.username} ({t.username})
                  </option>
                ))}
              </select>
            </div>
          </form>
        </Modal>
      )}

      {showEnrollModal && enrollSubject && (
        <Modal
          title={`Students in ${enrollSubject.code}`}
          onClose={() => setShowEnrollModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowEnrollModal(false)}>
                Done
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleEnrollmentChange(selectedStudentIds, true)}
                disabled={savingEnrollment || selectedStudentIds.length === 0}
                type="button"
              >
                {savingEnrollment ? <span className="spinner" /> : 'Remove selected'}
              </button>
              <button
                className="btn btn-primary"
                onClick={() => handleEnrollmentChange(selectedStudentIds, false)}
                disabled={savingEnrollment || selectedStudentIds.length === 0}
                type="button"
                id="enroll-selected-students"
              >
                {savingEnrollment ? <span className="spinner" /> : 'Enroll selected'}
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="student-search">
              Add students to this subject
            </label>
            <input
              id="student-search"
              className="form-input"
              type="text"
              placeholder="Search by name, ID, or program..."
              value={studentSearch}
              onChange={(e) => setStudentSearch(e.target.value)}
            />
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
                    onChange={() => toggleStudent(s.id)}
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
                        onClick={() => handleEnrollmentChange([s.id], true)}
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
      )}
    </div>
  )
}
