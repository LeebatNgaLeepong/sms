import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconEdit, IconTrash } from '../components/Icons'

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
  const { isAdmin } = useAuth()
  const { addToast } = useToast()

  useEffect(() => {
    fetchSubjects()
  }, [page, search])

  const fetchSubjects = async () => {
    setLoading(true)
    try {
      const res = await api.get('/subjects/', {
        params: { page, search: search || undefined },
      })
      setSubjects(res.data.results || res.data)
      setTotalCount(res.data.count || 0)
    } catch (err) {
      console.error('Subjects fetch error:', err)
    } finally {
      setLoading(false)
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
                  {isAdmin && (
                    <td>
                      <div className="table-actions">
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
          </form>
        </Modal>
      )}
    </div>
  )
}
