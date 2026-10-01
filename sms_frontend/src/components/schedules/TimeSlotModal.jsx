import Modal from '../Modal'

export default function TimeSlotModal({
  isOpen,
  onClose,
  editSlot,
  slotForm,
  setSlotForm,
  onSave,
  savingSlot,
  DAYS,
  endTimeInvalid,
}) {
  if (!isOpen) return null

  return (
    <Modal
      title={editSlot ? 'Edit Time Slot' : 'Add Time Slot'}
      onClose={onClose}
      onCancel={onClose}
      onSave={onSave}
      saving={savingSlot}
    >
      <form id="timeslot-form" onSubmit={onSave}>
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
            <label className="form-label" htmlFor="slot-end">End Time</label>
            <input
              id="slot-end"
              className={`form-input${endTimeInvalid ? ' error' : ''}`}
              type="time"
              value={slotForm.end_time}
              onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })}
              required
            />
            {endTimeInvalid && (
              <div className="form-error">End time must be after the start time.</div>
            )}
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
  )
}
