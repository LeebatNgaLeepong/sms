import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import StudentGradePanel from '../components/StudentGradePanel'
import GradeFormModal from '../components/GradeFormModal'
import { IconSearch } from '../components/Icons'
import { gwaColor } from '../utils/grades'

export default function GradesPage() {
  const [students, setStudents] = useState([])
  const [studentGrades, setStudentGrades] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingGrades, setLoadingGrades] = useState(false)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editGrade, setEditGrade] = useState(null)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const { isAdmin, isTeacher } = useAuth()
  const { addToast } = useToast()

  const canModify = isAdmin || isTeacher

  useEffect(() => {
    fetchStudents()
  }, [page, search])

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

  const openCreate = () => {
    setEditGrade(null)
    setShowModal(true)
  }

  const openEdit = (grade) => {
    setEditGrade(grade)
    setShowModal(true)
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
<GradeFormModal
        show={showModal}
        grade={editGrade}
        studentId={studentGrades?.student_id || ''}
        studentName={studentGrades?.student_name || ''}
        onClose={() => setShowModal(false)}
        onSaved={async () => {
          if (studentGrades) {
            const res = await api.get(`/students/${studentGrades.student_id}/grades/`)
            setStudentGrades(res.data)
          }
          fetchStudents()
        }}
      />
    </div>
  )
}