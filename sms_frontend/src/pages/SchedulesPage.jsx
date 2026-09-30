import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import {
  IconSearch,
  IconPlus,
  IconEdit,
  IconTrash,
  IconCalendar,
  IconRefresh,
} from '../components/Icons'

const DAYS = [
  { value: 'Mon', label: 'Mon', full: 'Monday' },
  { value: 'Tue', label: 'Tue', full: 'Tuesday' },
  { value: 'Wed', label: 'Wed', full: 'Wednesday' },
  { value: 'Thu', label: 'Thu', full: 'Thursday' },
  { value: 'Fri', label: 'Fri', full: 'Friday' },
  { value: 'Sat', label: 'Sat', full: 'Saturday' },
  { value: 'Sun', label: 'Sun', full: 'Sunday' },
]

const SLOT_TYPE_LABELS = { lec: 'Lecture', lab: 'Laboratory' }

const emptySlotForm = { day: 'Mon', start_time: '07:00', duration_hours: 2, slot_type: 'lec', label: '' }
const emptyScheduleForm = { student: '', subject: '', time_slot: '', semester: '', school_year: '' }

const formatTime = (value) => {
  if (!value) return ''
  const [h, m] = String(value).split(':')
  const hour = parseInt(h, 10)
  if (Number.isNaN(hour)) return value
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const display = hour % 12 === 0 ? 12 : hour % 12
  return `${display}:${m} ${suffix}`
}

const errorText = (err, fallback) => {
  const data = err.response?.data
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const detail = data.detail
    if (typeof detail === 'string') return detail
    return Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
      .join('. ')
  }
  return fallback
}

export default function SchedulesPage() {
  const { isAdmin, isTeacher, isStudent } = useAuth()
  const { addToast } = useToast()

  const [schedules, setSchedules] = useState([])
  const [timeSlots, setTimeSlots] = useState([])
  const [students, setStudents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [studentFilter, setStudentFilter] = useState('')
  const [showGrid, setShowGrid] = useState(true)
  const [regenerating, setRegenerating] = useState(false)

  const [showSlotModal, setShowSlotModal] = useState(false)
  const [editSlot, setEditSlot] = useState(null)
  const [slotForm, setSlotForm] = useState(emptySlotForm)
  const [savingSlot, setSavingSlot] = useState(false)

  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [editSchedule, setEditSchedule] = useState(null)
  const [scheduleForm, setScheduleForm] = useState(emptyScheduleForm)
  const [savingSchedule, setSavingSchedule] = useState(false)

  const loadReferenceData = useCallback(async () => {
    const requests = [api.get('/timeslots/', { params: { page_size: 500 } })]
    if (isAdmin || isTeacher) {
      requests.push(api.get('/students/', { params: { page_size: 200 } }))
      requests.push(api.get('/subjects/', { params: { page_size: 200 } }))
    }
    try {
      const [slotsRes, studentsRes, subjectsRes] = await Promise.all(requests)
      setTimeSlots(slotsRes.data.results || slotsRes.data || [])
      if (studentsRes) setStudents(studentsRes.data.results || studentsRes.data || [])
      if (subjectsRes) setSubjects(subjectsRes.data.results || subjectsRes.data || [])
    } catch (err) {
      console.error('Schedule reference data error:', err)
    }
  }, [isAdmin, isTeacher])

  const fetchSchedules = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/schedules/', {
        params: {
          page_size: 500,
          search: search || undefined,
          student: studentFilter || undefined,
        },
      })
      setSchedules(res.data.results || res.data || [])
    } catch (err) {
      console.error('Schedules fetch error:', err)
      addToast(errorText(err, 'Failed to load schedules'), 'error')
    } finally {
      setLoading(false)
    }
  }, [search, studentFilter, addToast])

  useEffect(() => {
    loadReferenceData()
  }, [loadReferenceData])

  useEffect(() => {
    fetchSchedules()
  }, [fetchSchedules])

  const slotRows = timeSlots
    .map((slot) => ({
      key: `${slot.day}-${slot.start_time}-${slot.duration_hours}`,
      startTime: slot.start_time,
      slots: timeSlots.filter((s) => s.start_time === slot.start_time),
    }))
    .reduce((acc, row) => {
      if (!acc.some((r) => r.startTime === row.startTime)) acc.push(row)
      return acc
    }, [])
    .sort((a, b) => a.startTime.localeCompare(b.startTime))

  const schedulesByCell = schedules.reduce((acc, item) => {
    const key = `${item.day}-${item.start_time}`
    if (!acc[key]) acc[key] = []
    acc[key].push(item)
    return acc
  }, {})

  const openCreateSlot = () => {
    setEditSlot(null)
    setSlotForm(emptySlotForm)
    setShowSlotModal(true)
  }

  const openEditSlot = (slot) => {
    setEditSlot(slot)
    setSlotForm({
      day: slot.day,
      start_time: String(slot.start_time).slice(0, 5),
      duration_hours: slot.duration_hours,
      slot_type: slot.slot_type,
      label: slot.label || '',
    })
    setShowSlotModal(true)
  }

  const handleSaveSlot = async (e) => {
    e.preventDefault()
    setSavingSlot(true)
    const payload = {
      day: slotForm.day,
      start_time: slotForm.start_time,
      duration_hours: parseInt(slotForm.duration_hours, 10) || 1,
      slot_type: slotForm.slot_type,
      label: slotForm.label,
    }
    try {
      if (editSlot) {
        await api.put(`/timeslots/${editSlot.id}/`, payload)
        addToast('Time slot updated', 'success')
      } else {
        await api.post('/timeslots/', payload)
        addToast('Time slot created', 'success')
      }
      setShowSlotModal(false)
      await loadReferenceData()
    } catch (err) {
      addToast(errorText(err, 'Failed to save time slot'), 'error')
    } finally {
      setSavingSlot(false)
    }
  }

  const handleDeleteSlot = async (slot) => {
    if (!window.confirm('Delete this time slot? Existing schedules using it will be removed.')) return
    try {
      await api.delete(`/timeslots/${slot.id}/`)
      addToast('Time slot deleted', 'success')
      await loadReferenceData()
      fetchSchedules()
    } catch (err) {
      addToast(errorText(err, 'Failed to delete time slot'), 'error')
    }
  }

  const openCreateSchedule = () => {
    setEditSchedule(null)
    setScheduleForm({ ...emptyScheduleForm, student: studentFilter || '' })
    setShowScheduleModal(true)
  }

  const openEditSchedule = (item) => {
    setEditSchedule(item)
    setScheduleForm({
      student: item.student,
      subject: item.subject,
      time_slot: item.time_slot,
      semester: item.semester || '',
      school_year: item.school_year || '',
    })
    setShowScheduleModal(true)
  }

  const handleSaveSchedule = async (e) => {
    e.preventDefault()
    setSavingSchedule(true)
    const payload = {
      student: parseInt(scheduleForm.student, 10),
      subject: parseInt(scheduleForm.subject, 10),
      time_slot: parseInt(scheduleForm.time_slot, 10),
      semester: scheduleForm.semester,
      school_year: scheduleForm.school_year,
    }
    try {
      if (editSchedule) {
        await api.put(`/schedules/${editSchedule.id}/`, payload)
        addToast('Schedule entry updated', 'success')
      } else {
        await api.post('/schedules/', payload)
        addToast('Schedule entry created', 'success')
      }
      setShowScheduleModal(false)
      fetchSchedules()
    } catch (err) {
      addToast(errorText(err, 'Failed to save schedule entry'), 'error')
    } finally {
      setSavingSchedule(false)
    }
  }

  const handleDeleteSchedule = async (item) => {
    if (!window.confirm(`Remove ${item.subject_code} from this schedule?`)) return
    try {
      await api.delete(`/schedules/${item.id}/`)
      addToast('Schedule entry removed', 'success')
      fetchSchedules()
    } catch (err) {
      addToast(errorText(err, 'Failed to remove schedule entry'), 'error')
    }
  }

  const handleGenerate = async () => {
    const targetIds = studentFilter ? [parseInt(studentFilter, 10)] : students.map((s) => s.id)
    if (targetIds.length === 0) {
      addToast('Select a student first, or create a student record', 'error')
      return
    }
    if (!window.confirm('Regenerate conflict-free schedules from enrolled subjects?')) return

    setRegenerating(true)
    try {
      const res = await api.post('/schedules/generate/', { student_ids: targetIds })
      const scheduled = (res.data.results || []).reduce(
        (sum, r) => sum + r.schedules.filter((s) => s.time_slot).length,
        0
      )
      addToast(`Schedules generated for ${targetIds.length} student(s) — ${scheduled} classes assigned`, 'success')
      fetchSchedules()
    } catch (err) {
      addToast(errorText(err, 'Failed to generate schedules'), 'error')
    } finally {
      setRegenerating(false)
    }
  }

  const currentDayIndex = new Date().getDay()
  const todayKey = currentDayIndex === 0 ? 'Sun' : DAYS[currentDayIndex - 1].value

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Schedules</h1>
          <p className="page-subtitle">
            {isStudent
              ? 'Your weekly class timetable'
              : `${schedules.length} scheduled class${schedules.length !== 1 ? 'es' : ''}`}
          </p>
        </div>
        {isAdmin && (
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              onClick={handleGenerate}
              disabled={regenerating}
              id="generate-schedule-btn"
            >
              {regenerating ? <span className="spinner" /> : <IconRefresh />} Auto-Generate
            </button>
            <button className="btn btn-primary" onClick={openCreateSchedule} id="add-schedule-btn">
              <IconPlus /> Add Entry
            </button>
          </div>
        )}
      </div>

      <div className="table-container" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Search subject or student..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              id="schedule-search"
            />
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', flexWrap: 'wrap' }}>
            {!isStudent && (
              <select
                className="filter-select"
                value={studentFilter}
                onChange={(e) => setStudentFilter(e.target.value)}
                id="schedule-student-filter"
              >
                <option value="">All students</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}
            <button className="btn btn-secondary btn-sm" onClick={() => setShowGrid(!showGrid)}>
              <IconCalendar /> {showGrid ? 'List View' : 'Grid View'}
            </button>
          </div>
        </div>

        {timeSlots.length === 0 && isAdmin && (
          <div style={{ padding: '0 var(--space-5)' }}>
            <div className="alert alert-warning" style={{ marginTop: 'var(--space-4)' }}>
              No time slots defined yet. Create time slots first so schedules can be generated.
            </div>
          </div>
        )}

        {loading ? (
          <div className="loading-page">
            <div className="spinner spinner-lg" />
          </div>
        ) : showGrid ? (
          slotRows.length === 0 ? (
            <div className="table-empty">No time slots available to build a timetable.</div>
          ) : (
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
                          {row.slots.map((s) => `${s.duration_hours}h`).filter((v, i, a) => a.indexOf(v) === i).join(' / ')}
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
                                    {formatTime(item.start_time)} &middot; {item.duration_hours}h
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
        ) : schedules.length === 0 ? (
          <div className="table-empty">No schedule entries found.</div>
        ) : (
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
                        <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEditSchedule(item)}>
                          <IconEdit />
                        </button>
                        <button className="btn-icon btn-ghost" title="Remove" onClick={() => handleDeleteSchedule(item)}>
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

      {isAdmin && (
        <div className="table-container">
          <div className="table-toolbar">
            <h3 style={{ fontSize: 'var(--font-base)', fontWeight: 600, color: 'var(--color-gray-800)' }}>
              Time Slots ({timeSlots.length})
            </h3>
            <button className="btn btn-secondary btn-sm" onClick={openCreateSlot} id="add-timeslot-btn">
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
                        <button className="btn-icon btn-ghost" title="Edit" onClick={() => openEditSlot(slot)}>
                          <IconEdit />
                        </button>
                        <button className="btn-icon btn-ghost" title="Delete" onClick={() => handleDeleteSlot(slot)}>
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
      )}

      {showSlotModal && (
        <Modal
          title={editSlot ? 'Edit Time Slot' : 'Add Time Slot'}
          onClose={() => setShowSlotModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowSlotModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSaveSlot}
                disabled={savingSlot}
                form="timeslot-form"
                type="submit"
              >
                {savingSlot ? <span className="spinner" /> : editSlot ? 'Update' : 'Create'}
              </button>
            </>
          }
        >
          <form id="timeslot-form" onSubmit={handleSaveSlot}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="slot-day">Day</label>
                <select
                  id="slot-day"
                  className="form-select"
                  value={slotForm.day}
                  onChange={(e) => setSlotForm({ ...slotForm, day: e.target.value })}
                >
                  {DAYS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.full}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="slot-start">Start Time</label>
                <input
                  id="slot-start"
                  className="form-input"
                  type="time"
                  value={slotForm.start_time}
                  onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="slot-duration">Duration (hours)</label>
                <input
                  id="slot-duration"
                  className="form-input"
                  type="number"
                  min="1"
                  max="8"
                  value={slotForm.duration_hours}
                  onChange={(e) => setSlotForm({ ...slotForm, duration_hours: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="slot-type">Type</label>
                <select
                  id="slot-type"
                  className="form-select"
                  value={slotForm.slot_type}
                  onChange={(e) => setSlotForm({ ...slotForm, slot_type: e.target.value })}
                >
                  <option value="lec">Lecture</option>
                  <option value="lab">Laboratory</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="slot-label">Label (optional)</label>
              <input
                id="slot-label"
                className="form-input"
                value={slotForm.label}
                onChange={(e) => setSlotForm({ ...slotForm, label: e.target.value })}
                placeholder="e.g., Period 1"
              />
            </div>
          </form>
        </Modal>
      )}

      {showScheduleModal && (
        <Modal
          title={editSchedule ? 'Edit Schedule Entry' : 'Add Schedule Entry'}
          onClose={() => setShowScheduleModal(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowScheduleModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSaveSchedule}
                disabled={savingSchedule}
                form="schedule-form"
                type="submit"
              >
                {savingSchedule ? <span className="spinner" /> : editSchedule ? 'Update' : 'Create'}
              </button>
            </>
          }
        >
          <form id="schedule-form" onSubmit={handleSaveSchedule}>
            <div className="form-group">
              <label className="form-label" htmlFor="schedule-student">Student</label>
              <select
                id="schedule-student"
                className="form-select"
                value={scheduleForm.student}
                onChange={(e) => setScheduleForm({ ...scheduleForm, student: e.target.value })}
                required
              >
                <option value="">Select student</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="schedule-subject">Subject</label>
              <select
                id="schedule-subject"
                className="form-select"
                value={scheduleForm.subject}
                onChange={(e) => setScheduleForm({ ...scheduleForm, subject: e.target.value })}
                required
              >
                <option value="">Select subject</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} &middot; {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="schedule-slot">Time Slot</label>
              <select
                id="schedule-slot"
                className="form-select"
                value={scheduleForm.time_slot}
                onChange={(e) => setScheduleForm({ ...scheduleForm, time_slot: e.target.value })}
                required
              >
                <option value="">Select time slot</option>
                {timeSlots.map((slot) => (
                  <option key={slot.id} value={slot.id}>
                    {DAYS.find((d) => d.value === slot.day)?.full} {formatTime(slot.start_time)} &middot;{' '}
                    {slot.duration_hours}h {SLOT_TYPE_LABELS[slot.slot_type]}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="schedule-semester">Semester</label>
                <input
                  id="schedule-semester"
                  className="form-input"
                  value={scheduleForm.semester}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, semester: e.target.value })}
                  placeholder="e.g., 1st Sem"
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="schedule-year">School Year</label>
                <input
                  id="schedule-year"
                  className="form-input"
                  value={scheduleForm.school_year}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, school_year: e.target.value })}
                  placeholder="e.g., 2025-2026"
                />
              </div>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
