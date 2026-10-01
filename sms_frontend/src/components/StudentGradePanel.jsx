import { IconPlus, IconEdit, IconTrash } from './Icons'
import { gradeBadgeClass, gradeDescription, gwaColor } from '../utils/grades'

/**
 * A single student's grades, shown after selecting their name on the Grades page.
 * Lets staff add, edit and delete that student's grades without leaving the view.
 */
export default function StudentGradePanel({
  data,
  loading,
  canModify,
  onBack,
  onAdd,
  onEdit,
  onDelete,
}) {
  const grades = data.grades || []

  return (
    <div>
      <button className="btn btn-ghost btn-sm back-link" onClick={onBack} id="grades-back-btn">
        &lsaquo; All students
      </button>

      <div className="page-header">
        <div>
          <h1 className="page-title">{data.student_name}</h1>
          <p className="page-subtitle">
            {data.student_id}
            {data.program ? ` · ${data.program}` : ''}
            {data.year_level ? ` · ${data.year_level}` : ''}
          </p>
        </div>
        {canModify && (
          <button className="btn btn-primary" onClick={onAdd} id="add-grade-btn">
            <IconPlus /> Record Grade
          </button>
        )}
      </div>

      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-card-label">GWA</div>
          <div className="stat-card-value" style={{ color: gwaColor(data.gwa ?? 5) }}>
            {(data.gwa ?? 5).toFixed(2)}
          </div>
          <div className="stat-hint">Weighted by units</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Simple GPA</div>
          <div className="stat-card-value" style={{ color: gwaColor(data.gpa ?? 5) }}>
            {(data.gpa ?? 5).toFixed(2)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Units Earned</div>
          <div className="stat-card-value">{data.units_earned ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Incomplete</div>
          <div className="stat-card-value">{data.incomplete_count ?? 0}</div>
          <div className="stat-hint">Not counted in GWA</div>
        </div>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : grades.length === 0 ? (
          <div className="table-empty">
            No grades recorded for this student yet.
          </div>
        ) : (
          <table className="data-table" id="student-grades-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Units</th>
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
                    <div style={{ fontWeight: 500 }}>{g.subject.code}</div>
                    <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>
                      {g.subject.name}
                    </div>
                  </td>
                  <td>{g.subject.units}</td>
<td>
                      <div style={{ fontWeight: 500 }}>{g.score ?? '—'}</div>
                      {g.remark && (
                        <div
                          style={{
                            fontSize: 'var(--font-xs)',
                            color: 'var(--color-gray-400)',
                            maxWidth: 180,
                          }}
                          title={g.remark}
                        >
                          {g.remark}
                        </div>
                      )}
                    </td>
                  <td>
                    <span
                      className={gradeBadgeClass(g.letter)}
                      title={gradeDescription(g.letter)}
                    >
                      {g.letter}
                    </span>
                  </td>
                  <td>{g.grade_points ?? '—'}</td>
                  <td style={{ color: 'var(--color-gray-500)' }}>{g.recorded_by || '—'}</td>
                  {canModify && (
                    <td>
                      <div className="table-actions">
                        <button
                          className="btn-icon btn-ghost"
                          title="Edit"
                          onClick={() => onEdit(g)}
                        >
                          <IconEdit />
                        </button>
                        <button
                          className="btn-icon btn-ghost"
                          title="Delete"
                          onClick={() => onDelete(g)}
                        >
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
      </div>
    </div>
  )
}
