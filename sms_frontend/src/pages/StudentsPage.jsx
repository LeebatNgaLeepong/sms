import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconEdit, IconTrash, IconEye } from '../components/Icons'

export default function StudentsPage() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editStudent, setEditStudent] = useState(null)
  const [form, setForm] = useState({ name: '', email: '', program: '', year_level: '' })
  const [saving, setSaving] = useState(false)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const { isAdmin } = useAuth()
  const { addToast } = useToast()
  const navigate = useNavigate()

  useEffect(() => {
    fetchStudents()
  }, [page, search])

  const fetchStudents = async () => {
    setLoading(true)
    try {
      const res = await api.get('/students/', {
        params: { page, search: search || undefined },
      })
      setStudents(res.data.results || res.data)
      setTotalCount(res.data.count || 0)
    } catch (err) {
      console.error('Students fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setEditStudent(null)
    setForm({ name: '', email: '', program: '', year_level: '' })
    setShowModal(true)
  }

  const openEdit = (student) => {
    setEditStudent(student)
    setForm({
      name: student.name,
      email: student.email,
      program: student.program,
      year_level: student.year_level,
    })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (editStudent) {
        await api.put(`/students/${editStudent.id}/`, form)
        addToast('Student updated successfully', 'success')
      } else {
        await api.post('/students/', form)
        addToast('Student created successfully', 'success')
      }
      setShowModal(false)
      fetchStudents()
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

  const handleDelete = async (student) => {
    if (!window.confirm(`Delete student ${student.name}?`)) return
    try {
      await api.delete(`/students/${student.id}/`)
      addToast('Student deleted', 'success')
      fetchStudents()
    } catch {
      addToast('Failed to delete student', 'error')
    }
  }

  const totalPages = Math.ceil(totalCount / 10)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Students
          </h1>
          <p className="page-subtitle">
            {totalCount} student{totalCount !== 1 ? 's' : ''} registered
          </p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={openCreate} id="add-student-btn">
            <IconPlus /> Add Student
          </button>
        )}
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Search students..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              id="student-search"
            />
          </div>
        </div>

        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : students.length === 0 ? (
          <div className="table-empty">No students found.</div>
        ) : (
          <table className="data-table" id="students-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Program</th>
                <th>Year</th>
                <th>GPA</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>{s.id}</td>
                  <td>{s.name}</td>
                  <td>{s.email}</td>
                  <td>{s.program}</td>
                  <td>{s.year_level}</td>
                  <td>
                    <span style={{ fontWeight: 600, color: s.gpa >= 3 ? 'var(--color-success)' : s.gpa >= 2 ? 'var(--color-gold-600)' : 'var(--color-error)' }}>
                      {(s.gpa || 0).toFixed(2)}
                    </span>
                  </td>
                  <td>
                    <div className="table-actions">
                      <button
                        className="btn-icon btn-ghost"
                        title="View grades"
                        onClick={() => navigate(`/students/${s.id}`)}
                      >
                        <IconEye />
                      </button>
                      {isAdmin && (
                        <>
                          <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEdit(s)}>
                            <IconEdit />
                          </button>
                          <button className="btn-icon btn-ghost" title="Delete" onClick={() => handleDelete(s)}>
                            <IconTrash />
                          </button>
                        </>
                      )}
                    </div>
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

      {showModal && (
        <Modal
          title={editStudent ? 'Edit Student' : 'Add Student'}
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saving}
                form="student-form"
                type="submit"
              >
                {saving ? <span className="spinner" /> : editStudent ? 'Update' : 'Create'}
              </button>
            </>
          }
        >
          <form id="student-form" onSubmit={handleSave}>
            <div className="form-group">
              <label className="form-label" htmlFor="student-name">Full Name</label>
              <input
                id="student-name"
                className="form-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="student-email">Email</label>
              <input
                id="student-email"
                className="form-input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="student-program">Program</label>
                <input
                  id="student-program"
                  className="form-input"
                  value={form.program}
                  onChange={(e) => setForm({ ...form, program: e.target.value })}
                  required
                  placeholder="e.g., BS Computer Science"
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="student-year">Year Level</label>
                <select
                  id="student-year"
                  className="form-select"
                  value={form.year_level}
                  onChange={(e) => setForm({ ...form, year_level: e.target.value })}
                  required
                >
                  <option value="">Select year</option>
                  <option value="1st Year">1st Year</option>
                  <option value="2nd Year">2nd Year</option>
                  <option value="3rd Year">3rd Year</option>
                  <option value="4th Year">4th Year</option>
                </select>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
