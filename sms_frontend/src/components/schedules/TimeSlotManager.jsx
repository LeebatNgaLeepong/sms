import { IconPlus, IconEdit, IconTrash } from '../Icons'

export default function TimeSlotManager({
  timeSlots,
  DAYS,
  SLOT_TYPE_LABELS,
  formatTime,
  onAddSlot,
  onEditSlot,
  onDeleteSlot,
}) {
  return (
    <div className="table-container">
      <div className="table-toolbar">
        <h3 style={{ fontSize: 'var(--font-base)', fontWeight: 600, color: 'var(--color-gray-800)' }}>
          Time Slots ({timeSlots.length})
        </h3>
        <button className="btn btn-secondary btn-sm" onClick={onAddSlot} id="add-timeslot-btn">
          <IconPlus /> Add Time Slot
        </button>
      </div>

      {timeSlots.length === 0 ? (
        <div className="table-empty">No time slots defined.</div>
      ) : (
        <table className="data-table" id="timeslots-table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Start</th>
              <th>End</th>
              <th>Duration</th>
              <th>Type</th>
              <th>Label</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {timeSlots.map((slot) => (
              <tr key={slot.id}>
                <td style={{ fontWeight: 500 }}>
                  {DAYS.find((d) => d.value === slot.day)?.full || slot.day}
                </td>
                <td>{formatTime(slot.start_time)}</td>
                <td>{formatTime(slot.end_time)}</td>
                <td>{slot.duration_hours}h</td>
                <td>
                  <span className={`badge ${slot.slot_type === 'lab' ? 'badge-lab' : 'badge-lec'}`}>
                    {SLOT_TYPE_LABELS[slot.slot_type] || slot.slot_type}
                  </span>
                </td>
                <td style={{ color: 'var(--color-gray-500)' }}>{slot.label || '—'}</td>
                <td>
                  <div className="table-actions">
                    <button className="btn-icon btn-ghost" title="Edit" onClick={() => onEditSlot(slot)}>
                      <IconEdit />
                    </button>
                    <button className="btn-icon btn-ghost" title="Delete" onClick={() => onDeleteSlot(slot)}>
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
  )
}
