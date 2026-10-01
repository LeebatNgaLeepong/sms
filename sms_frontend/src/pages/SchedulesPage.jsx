import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import useTerms from '../hooks/useTerms'
import {
  IconSearch,
  IconPlus,
  IconCalendar,
  IconRefresh,
} from '../components/Icons'
import ScheduleWeeklyGrid from '../components/schedules/ScheduleWeeklyGrid'
import ScheduleListView from '../components/schedules/ScheduleListView'
import TimeSlotManager from '../components/schedules/TimeSlotManager'
import TimeSlotModal from '../components/schedules/TimeSlotModal'
import ScheduleEntryModal from '../components/schedules/ScheduleEntryModal'

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

const emptySlotForm = { day: 'Mon', start_time: '07:00', end_time: '09:00', slot_type: 'lec', label: '' }
const emptyScheduleForm = {
  student: '',
  subject: '',
  section: '',
  time_slot: '',
  semester: '',
  school_year: '',
}

const formatTime = (value) => {
  if (!value) return ''
  const [h, m] = String(value).split(':')
  const hour = parseInt(h, 10)
  if (Number.isNaN(hour)) return value
  const suffix = hour >= 12 ? 'PM' : 'AM'
  const display = hour % 12 === 0 ? 12 : hour % 12
  return `${display}:${m} ${suffix}`
}

/** Compare "HH:MM" strings; returns true when end is not after start. */
const isEndBeforeStart = (start, end) => {
  if (!start || !end) return false
  return end <= start
}

/** Human-readable length between two "HH:MM" strings, e.g. "2h" or "1h 30m". */
const formatDuration = (start, end) => {
  if (isEndBeforeStart(start, end)) return '—'
  const [sh, sm] = start.split(':').map(Number)
  const [eh, em] = end.split(':').map(Number)
  const minutes = eh * 60 + em - (sh * 60 + sm)
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours && rest) return `${hours}h ${rest}m`
  if (hours) return `${hours}h`
  return `${rest}m`
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
  const { current, semesters, school_years: schoolYears } = useTerms()

  const [term, setTerm] = useState(current)
  const [schedules, setSchedules] = useState([])
  const [timeSlots, setTimeSlots] = useState([])
  const [students, setStudents] = useState([])
  const [subjects, setSubjects] = useState([])
  const [sections, setSections] = useState([])
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
    const requests = [
      api.get('/timeslots/', { params: { page_size: 500 } }),
      api.get('/sections/', { params: { page_size: 500 } }),
    ]
    if (isAdmin || isTeacher) {
      requests.push(api.get('/students/', { params: { page_size: 200 } }))
      requests.push(api.get('/subjects/', { params: { page_size: 200 } }))
    }
    try {
      const [slotsRes, sectionsRes, studentsRes, subjectsRes] = await Promise.all(requests)
      setTimeSlots(slotsRes.data.results || slotsRes.data || [])
      setSections(sectionsRes.data.results || sectionsRes.data || [])
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
          semester: term.semester,
          school_year: term.school_year,
        },
      })
      setSchedules(res.data.results || res.data || [])
    } catch (err) {
      console.error('Schedules fetch error:', err)
      addToast(errorText(err, 'Failed to load schedules'), 'error')
    } finally {
      setLoading(false)
    }
  }, [search, studentFilter, term.semester, term.school_year, addToast])

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
      end_time: String(slot.end_time).slice(0, 5),
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
      end_time: slotForm.end_time,
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
    setScheduleForm({
      ...emptyScheduleForm,
      student: studentFilter || '',
      semester: term.semester,
      school_year: term.school_year,
    })
    setShowScheduleModal(true)
  }

  const openEditSchedule = (item) => {
    setEditSchedule(item)
    setScheduleForm({
      student: item.student_id,
      subject: item.subject,
      section: item.section || '',
      time_slot: item.time_slot,
      semester: item.semester || term.semester,
      school_year: item.school_year || term.school_year,
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
    if (scheduleForm.section) payload.section = parseInt(scheduleForm.section, 10)
    try {
      const res = editSchedule
        ? await api.put(`/schedules/${editSchedule.id}/`, payload)
        : await api.post('/schedules/', payload)
      addToast(
        res.data?.moved
          ? 'Already scheduled this subject — class time updated'
          : editSchedule
            ? 'Schedule entry updated'
            : 'Schedule entry created',
        'success'
      )
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
      const res = await api.post('/schedules/generate/', {
        student_ids: targetIds,
        semester: term.semester,
        school_year: term.school_year,
      })
      const classes = res.data?.classes_scheduled ?? 0
      const groups = res.data?.subjects_scheduled ?? 0
      addToast(
        `Generated ${classes} class${classes !== 1 ? 'es' : ''} across ${groups} section${
          groups !== 1 ? 's' : ''
        } for ${res.data?.term || `${term.semester} ${term.school_year}`}`,
        'success'
      )
      fetchSchedules()
    } catch (err) {
      addToast(errorText(err, 'Failed to generate schedules'), 'error')
    } finally {
      setRegenerating(false)
    }
  }

  const currentDayIndex = new Date().getDay()
  const todayKey = currentDayIndex === 0 ? 'Sun' : DAYS[currentDayIndex - 1].value
  const endTimeInvalid = isEndBeforeStart(slotForm.start_time, slotForm.end_time)
  const subjectSections = sections.filter(
    (s) => String(s.subject) === String(scheduleForm.subject)
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Schedules</h1>
          <p className="page-subtitle">
            {isStudent
              ? 'Your weekly class timetable'
              : `${schedules.length} scheduled class${schedules.length !== 1 ? 'es' : ''} in ${term.semester} ${term.school_year}`}
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
            <select
              className="filter-select"
              value={term.semester}
              onChange={(e) => setTerm({ ...term, semester: e.target.value })}
              id="schedule-term-semester"
              title="Semester"
            >
              {semesters.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <select
              className="filter-select"
              value={term.school_year}
              onChange={(e) => setTerm({ ...term, school_year: e.target.value })}
              id="schedule-term-year"
              title="School Year"
            >
              {schoolYears.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
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
          <ScheduleWeeklyGrid
            slotRows={slotRows}
            schedulesByCell={schedulesByCell}
            todayKey={todayKey}
            DAYS={DAYS}
            isStudent={isStudent}
            formatTime={formatTime}
            formatDuration={formatDuration}
          />
        ) : (
          <ScheduleListView
            schedules={schedules}
            DAYS={DAYS}
            isStudent={isStudent}
            isAdmin={isAdmin}
            formatTime={formatTime}
            SLOT_TYPE_LABELS={SLOT_TYPE_LABELS}
            onEdit={openEditSchedule}
            onDelete={handleDeleteSchedule}
          />
        )}
      </div>

      {isAdmin && (
        <TimeSlotManager
          timeSlots={timeSlots}
          DAYS={DAYS}
          SLOT_TYPE_LABELS={SLOT_TYPE_LABELS}
          formatTime={formatTime}
          onAddSlot={openCreateSlot}
          onEditSlot={openEditSlot}
          onDeleteSlot={handleDeleteSlot}
        />
      )}

      <TimeSlotModal
        isOpen={showSlotModal}
        onClose={() => setShowSlotModal(false)}
        editSlot={editSlot}
        slotForm={slotForm}
        setSlotForm={setSlotForm}
        onSave={handleSaveSlot}
        savingSlot={savingSlot}
        DAYS={DAYS}
        endTimeInvalid={endTimeInvalid}
      />

      <ScheduleEntryModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        editSchedule={editSchedule}
        scheduleForm={scheduleForm}
        setScheduleForm={setScheduleForm}
        onSave={handleSaveSchedule}
        savingSchedule={savingSchedule}
        students={students}
        subjects={subjects}
        subjectSections={subjectSections}
        timeSlots={timeSlots}
        DAYS={DAYS}
        formatTime={formatTime}
        SLOT_TYPE_LABELS={SLOT_TYPE_LABELS}
      />
    </div>
  )
}
