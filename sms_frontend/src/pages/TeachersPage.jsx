import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconEdit, IconTrash } from '../components/Icons'

export default function TeachersPage() {
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editTeacher, setEditTeacher] = useState(null)
  const [form, setForm] = useState({ first_name: '', last_name: '', username: '', email: '', password: '' })
  const [saving, setSaving] = useState(false)
  const { isAdmin } = useAuth()
  const { addToast } = useToast()

  useEffect(() => { fetchTeachers() }, [])

  const fetchTeachers = async () => {
    setLoading(true)
    try {
      const res = await api.get('/teachers/')
      setTeachers(res.data)
    } catch (err) {
      console.error('Teachers fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setEditTeacher(null)
    setForm({ first_name: '', last_name: '', username: '', email: '', password: '' })
    setShowModal(true)
  }

  const openEdit = (t) => {
    setEditTeacher(t)
    setForm({ first_name: t.first_name, last_name: t.last_name, username: t.username, email: t.email, password: '' })
    setShowModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (editTeacher) {
        await api.put(`/teachers/${editTeacher.id}/`, form)
        addToast('Teacher updated successfully', 'success')
      } else {
        await api.post('/teachers/', form)
        addToast('Teacher added successfully', 'success')
      }
      setShowModal(false)
      fetchTeachers()
    } catch (err) {
      const msg = err.response?.data
      const errorText = typeof msg === 'object'
        ? Object.entries(msg).map(([k, v]) => (Array.isArray(v) ? v.join(', ') : v)).join('. ')
        : 'An error occurred'
      addToast(errorText, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (t) => {
    if (!window.confirm(`Delete teacher ${t.username}? This cannot be undone.`)) return
    try {
      await api.delete(`/teachers/${t.id}/`)
      addToast('Teacher deleted', 'success')
      fetchTeachers()
    } catch {
      addToast('Failed to delete teacher', 'error')
    }
  }

  const filtered = teachers.filter(t =>
    `${t.first_name} ${t.last_name} ${t.username} ${t.email}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  if (!isAdmin) {
    return (
      <div className="loading-page">
        <p style={{ color: 'var(--color-gray-500)' }}>Access restricted to administrators.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Teachers</h1>
          <p className="page-subtitle">{teachers.length} teacher{teachers.length !== 1 ? 's' : ''}</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate} id="add-teacher-btn">
          <IconPlus /> Add Teacher
        </button>
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Search teachers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              id="teacher-search"
            />
          </div>
        </div>

        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : filtered.length === 0 ? (
          <div className="table-empty">No teachers found.</div>
        ) : (
          <table className="data-table" id="teachers-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Username</th>
                <th>Email</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td>
                    <div style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>
                      {t.first_name || t.last_name ? `${t.first_name} ${t.last_name}`.trim() : '—'}
                    </div>
                  </td>
                  <td style={{ color: 'var(--color-gray-600)', fontFamily: 'monospace', fontSize: 'var(--font-sm)' }}>
                    @{t.username}
                  </td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{t.email || '—'}</td>
                  <td style={{ color: 'var(--color-gray-400)', fontSize: 'var(--font-sm)' }}>
                    {new Date(t.date_joined).toLocaleDateString()}
                  </td>
                  <td>
                    <div className="table-actions">
                      <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEdit(t)}>
                        <IconEdit />
                      </button>
                      <button className="btn-icon btn-ghost" title="Delete" onClick={() => handleDelete(t)}>
                        <IconTrash />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <Modal
          title={editTeacher ? 'Edit Teacher' : 'Add Teacher'}
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} form="teacher-form" type="submit">
                {saving ? <span className="spinner" /> : editTeacher ? 'Update' : 'Create'}
              </button>
            </>
          }
        >
          <form id="teacher-form" onSubmit={handleSave}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="teacher-fname">First Name</label>
                <input
                  id="teacher-fname"
                  className="form-input"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  placeholder="e.g., Maria"
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="teacher-lname">Last Name</label>
                <input
                  id="teacher-lname"
                  className="form-input"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  placeholder="e.g., Santos"
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="teacher-username">Username *</label>
              <input
                id="teacher-username"
                className="form-input"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
                placeholder="e.g., msantos"
                disabled={!!editTeacher}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="teacher-email">Email</label>
              <input
                id="teacher-email"
                className="form-input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="e.g., msantos@school.edu"
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="teacher-password">
                {editTeacher ? 'New Password (leave blank to keep)' : 'Password *'}
              </label>
              <input
                id="teacher-password"
                className="form-input"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required={!editTeacher}
                placeholder="Minimum 8 characters"
              />
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
