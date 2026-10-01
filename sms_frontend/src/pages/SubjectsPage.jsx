import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { IconSearch, IconPlus, IconEdit, IconTrash, IconStudents } from '../components/Icons'
import SubjectModal from '../components/subjects/SubjectModal'
import SectionManagerModal from '../components/subjects/SectionManagerModal'
import SectionRosterModal from '../components/subjects/SectionRosterModal'

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

  const [showSectionModal, setShowSectionModal] = useState(false)
  const [sectionSubject, setSectionSubject] = useState(null)
  const [sections, setSections] = useState([])
  const [sectionCounts, setSectionCounts] = useState({})
  const [sectionForm, setSectionForm] = useState({ code: '', capacity: 40, instructor: '' })
  const [savingSection, setSavingSection] = useState(false)

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

  const loadEnrolledCounts = async (list) => {
    if (!isAdmin) return
    const entries = await Promise.all(
      list.map(async (s) => {
        try {
          const [enrolledRes, sectionsRes] = await Promise.all([
            api.get(`/subjects/${s.id}/students/`),
            api.get('/sections/', { params: { subject: s.id, page_size: 100 } }),
          ])
          return [s.id, enrolledRes.data.count, (sectionsRes.data.results || []).length]
        } catch {
          return [s.id, null, null]
        }
      })
    )
    setEnrolledCounts(Object.fromEntries(entries.map(([id, count]) => [id, count ?? 0])))
    setSectionCounts(Object.fromEntries(entries.map(([id, , sc]) => [id, sc ?? 0])))
  }

  const openSections = async (subject) => {
    setSectionSubject(subject)
    setSectionForm({ code: '', capacity: 40, instructor: '' })
    setShowSectionModal(true)
    try {
      const res = await api.get('/sections/', { params: { subject: subject.id, page_size: 100 } })
      setSections(res.data.results || res.data || [])
    } catch (err) {
      console.error('Sections fetch error:', err)
      setSections([])
    }
  }

  const handleAddSection = async (e) => {
    e.preventDefault()
    if (!sectionForm.code.trim()) return
    setSavingSection(true)
    try {
      const res = await api.post('/sections/', {
        subject: sectionSubject.id,
        code: sectionForm.code.trim().toUpperCase(),
        capacity: parseInt(sectionForm.capacity, 10) || 40,
        instructor: sectionForm.instructor || null,
      })
      addToast(`Created section ${sectionSubject.code}-${res.data.code}`, 'success')
      setSectionForm({ code: '', capacity: 40, instructor: '' })
      const listRes = await api.get('/sections/', {
        params: { subject: sectionSubject.id, page_size: 100 },
      })
      setSections(listRes.data.results || [])
      setSectionCounts((prev) => ({ ...prev, [sectionSubject.id]: sections.length + 1 }))
    } catch (err) {
      addToast(err.response?.data?.code?.[0] || 'Failed to create section', 'error')
    } finally {
      setSavingSection(false)
    }
  }

  const handleDeleteSection = async (section) => {
    if (
      !window.confirm(
        `Delete section ${section.code}? Its students keep the subject but lose this class.`
      )
    )
      return
    try {
      await api.delete(`/sections/${section.id}/`)
      setSections((prev) => prev.filter((s) => s.id !== section.id))
      setSectionCounts((prev) => ({ ...prev, [sectionSubject.id]: sections.length - 1 }))
      addToast(`Deleted section ${section.code}`, 'success')
    } catch (err) {
      addToast('Failed to delete section', 'error')
    }
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

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Subjects</h1>
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
                <th>Sections</th>
                <th>Enrolled</th>
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
                      onClick={() => openSections(s)}
                      title="Manage sections of this subject"
                      id={`manage-sections-${s.code}`}
                    >
                      {sectionCounts[s.id] ?? 0} section{sectionCounts[s.id] === 1 ? '' : 's'}
                    </button>
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => openEnrollment(s)}
                      id={`manage-students-${s.code}`}
                    >
                      <IconStudents /> {enrolledCounts[s.id] ?? 0}
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

      <SubjectModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        editSubject={editSubject}
        form={form}
        setForm={setForm}
        teachers={teachers}
        onSave={handleSave}
        saving={saving}
      />

      <SectionManagerModal
        isOpen={showSectionModal}
        onClose={() => setShowSectionModal(false)}
        subject={sectionSubject}
        sections={sections}
        sectionForm={sectionForm}
        setSectionForm={setSectionForm}
        teachers={teachers}
        isAdmin={isAdmin}
        onAddSection={handleAddSection}
        onDeleteSection={handleDeleteSection}
        savingSection={savingSection}
      />

      <SectionRosterModal
        isOpen={showEnrollModal}
        onClose={() => setShowEnrollModal(false)}
        subject={enrollSubject}
        enrolledStudents={enrolledStudents}
        allStudents={allStudents}
        selectedStudentIds={selectedStudentIds}
        onToggleStudent={toggleStudent}
        onEnrollmentChange={handleEnrollmentChange}
        savingEnrollment={savingEnrollment}
        isAdmin={isAdmin}
      />
    </div>
  )
}
