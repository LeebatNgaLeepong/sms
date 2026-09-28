import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import {
  IconStudents,
  IconSubjects,
  IconGrades,
  IconTeacher,
  IconPercent,
} from '../components/Icons'

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/dashboard/summary/')
      setData(res.data)
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-page">
        <div className="spinner spinner-lg" />
        <span>Loading dashboard...</span>
      </div>
    )
  }

  if (!data) {
    return <div className="loading-page">Failed to load dashboard data.</div>
  }

  const maxGrade = Math.max(
    data.grade_distribution.A,
    data.grade_distribution.B,
    data.grade_distribution.C,
    data.grade_distribution.D,
    data.grade_distribution.F,
    1
  )

  return (
    <div>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h1 style={{ fontSize: 'var(--font-xl)', fontWeight: 600, color: 'var(--color-gray-900)' }}>
          Dashboard
        </h1>
        <p style={{ fontSize: 'var(--font-sm)', color: 'var(--color-gray-500)', marginTop: '4px' }}>
          Welcome back, {user?.first_name || user?.username}
        </p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Total Students</span>
            <div className="stat-card-icon red"><IconStudents /></div>
          </div>
          <div className="stat-card-value">{data.total_students}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Total Subjects</span>
            <div className="stat-card-icon gold"><IconSubjects /></div>
          </div>
          <div className="stat-card-value">{data.total_subjects}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Total Teachers</span>
            <div className="stat-card-icon blue"><IconTeacher /></div>
          </div>
          <div className="stat-card-value">{data.total_teachers}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Average GPA</span>
            <div className="stat-card-icon green"><IconGrades /></div>
          </div>
          <div className="stat-card-value">{data.average_gpa.toFixed(2)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Grades Recorded</span>
            <div className="stat-card-icon gold"><IconGrades /></div>
          </div>
          <div className="stat-card-value">{data.total_grades}</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Passing Rate</span>
            <div className="stat-card-icon green"><IconPercent /></div>
          </div>
          <div className="stat-card-value">{data.passing_rate}%</div>
        </div>
      </div>

      <div className="chart-card">
        <h3 className="chart-card-title">Grade Distribution</h3>
        <div className="grade-bars">
          {['A', 'B', 'C', 'D', 'F'].map((letter) => (
            <div key={letter} className="grade-bar-row">
              <span className="grade-bar-label">{letter}</span>
              <div className="grade-bar-track">
                <div
                  className={`grade-bar-fill ${letter.toLowerCase()}`}
                  style={{
                    width: `${(data.grade_distribution[letter] / maxGrade) * 100}%`,
                  }}
                />
              </div>
              <span className="grade-bar-count">{data.grade_distribution[letter]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
