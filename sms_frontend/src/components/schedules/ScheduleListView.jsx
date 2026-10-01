import { IconEdit, IconTrash } from '../Icons'

export default function ScheduleListView({
  schedules,
  DAYS,
  isStudent,
  isAdmin,
  formatTime,
  SLOT_TYPE_LABELS,
  onEdit,
  onDelete,
}) {
  if (schedules.length === 0) {
    return <div className="table-empty">No schedule entries found.</div>
  }

  return (
    <table className="data-table" id="schedules-table">
      <thead>
        <tr>
          <th>Day</th>
          <th>Time</th>
          {!isStudent && <th>Student</th>}
          <th>Subject</th>
          <th>Type</th>
          <th>Semester</th>
          {isAdmin && <th>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {schedules.map((item) => (
          <tr key={item.id}>
            <td style={{ fontWeight: 500 }}>
              {DAYS.find((d) => d.value === item.day)?.full || item.day}
            </td>
            <td style={{ whiteSpace: 'nowrap' }}>
              {formatTime(item.start_time)} &ndash; {formatTime(item.end_time)}
            </td>
            {!isStudent && <td>{item.student_name}</td>}
            <td>
              <div style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>{item.subject_code}</div>
              <div style={{ color: 'var(--color-gray-500)' }}>{item.subject_name}</div>
            </td>
            <td>
              <span className={`badge ${item.slot_type === 'lab' ? 'badge-lab' : 'badge-lec'}`}>
                {SLOT_TYPE_LABELS[item.slot_type] || item.slot_type}
              </span>
            </td>
            <td style={{ color: 'var(--color-gray-600)' }}>
              {item.semester || '—'}
              {item.school_year ? ` · ${item.school_year}` : ''}
            </td>
            {isAdmin && (
              <td>
                <div className="table-actions">
                  <button className="btn-icon btn-ghost" title="Edit" onClick={() => onEdit(item)}>
                    <IconEdit />
                  </button>
                  <button className="btn-icon btn-ghost" title="Remove" onClick={() => onDelete(item)}>
                    <IconTrash />
                  </button>
                </div>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
