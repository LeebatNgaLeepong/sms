import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'
import { IconChevronLeft } from '../components/Icons'

export default function StudentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStudentGrades()
  }, [id])

  const fetchStudentGrades = async () => {
    try {
      const res = await api.get(`/students/${id}/grades/`)
      setData(res.data)
    } catch (err) {
      console.error('Student detail fetch error:', err)
    } finally {
      setLoading(false)
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

  const letterClass = (letter) => `badge badge-${letter.toLowerCase()}`

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
          <div className="detail-field-label">GPA</div>
          <div className="detail-field-value" style={{
            color: data.gpa >= 3 ? 'var(--color-success)' : data.gpa >= 2 ? 'var(--color-gold-600)' : 'var(--color-error)'
          }}>
            {data.gpa.toFixed(2)}
          </div>
        </div>
        <div className="detail-field">
          <div className="detail-field-label">Total Grades</div>
          <div className="detail-field-value">{data.total_grades}</div>
        </div>
      </div>

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
                  <td><span className={letterClass(g.letter)}>{g.letter}</span></td>
                  <td>{g.grade_points}</td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{g.recorded_by || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
