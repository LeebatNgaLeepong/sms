export default function ScheduleWeeklyGrid({
  slotRows,
  schedulesByCell,
  todayKey,
  DAYS,
  isStudent,
  formatTime,
  formatDuration,
}) {
  if (slotRows.length === 0) {
    return <div className="table-empty">No time slots available to build a timetable.</div>
  }

  return (
    <div className="timetable-wrap">
      <table className="timetable" id="schedule-timetable">
        <thead>
          <tr>
            <th className="timetable-time-col">Time</th>
            {DAYS.map((d) => (
              <th key={d.value} className={d.value === todayKey ? 'timetable-today' : ''}>
                {d.full}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {slotRows.map((row) => (
            <tr key={row.startTime}>
              <td className="timetable-time-col">
                {formatTime(row.startTime)}
                <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>
                  {row.slots
                    .map((s) => formatDuration(String(s.start_time).slice(0, 5), String(s.end_time).slice(0, 5)))
                    .filter((v, i, a) => a.indexOf(v) === i)
                    .join(' / ')}
                </div>
              </td>
              {DAYS.map((day) => {
                const cellKey = `${day.value}-${row.startTime}`
                const items = schedulesByCell[cellKey] || []
                const isToday = day.value === todayKey
                return (
                  <td key={day.value} className={isToday ? 'timetable-today' : ''}>
                    {items.length === 0 ? (
                      <span className="timetable-empty">&mdash;</span>
                    ) : (
                      items.map((item) => (
                        <div
                          key={item.id}
                          className={`timetable-card ${item.slot_type === 'lab' ? 'lab' : 'lec'}`}
                        >
                          <div className="timetable-card-code">{item.subject_code}</div>
                          <div className="timetable-card-name">{item.subject_name}</div>
                          <div className="timetable-card-meta">
                            {formatTime(item.start_time)} &ndash; {formatTime(item.end_time)}
                            {item.slot_type === 'lab' ? ' Lab' : ''}
                          </div>
                          {!isStudent && (
                            <div className="timetable-card-meta">{item.student_name}</div>
                          )}
                        </div>
                      ))
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
