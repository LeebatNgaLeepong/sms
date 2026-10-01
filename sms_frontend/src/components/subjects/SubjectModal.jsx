import Modal from '../Modal'

export default function SubjectModal({
  isOpen,
  onClose,
  editSubject,
  form,
  setForm,
  teachers,
  onSave,
  saving,
}) {
  if (!isOpen) return null

  return (
    <Modal
      title={editSubject ? 'Edit Subject' : 'Add Subject'}
      onClose={onClose}
      onCancel={onClose}
      onSave={onSave}
      saving={saving}
    >
      <form id="subject-form" onSubmit={onSave}>
        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="subject-code">Course Code</label>
            <input
              id="subject-code"
              className="form-input"
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              required
              placeholder="e.g., CS101"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="subject-units">Units</label>
            <input
              id="subject-units"
              className="form-input"
              type="number"
              min="1"
              max="12"
              value={form.units}
              onChange={(e) => setForm({ ...form, units: parseInt(e.target.value) || 1 })}
              required
            />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="subject-name">Subject Name</label>
          <input
            id="subject-name"
            className="form-input"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            placeholder="e.g., Introduction to Programming"
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="subject-instructor">Assigned Instructor</label>
          <select
            id="subject-instructor"
            className="form-select"
            value={form.instructor || ''}
            onChange={(e) => setForm({ ...form, instructor: e.target.value ? parseInt(e.target.value) : '' })}
          >
            <option value="">No Instructor Assigned</option>
            {teachers.map((t) => (
              <option key={t.id} value={t.id}>
                {t.first_name ? `${t.first_name} ${t.last_name}` : t.username} ({t.username})
              </option>
            ))}
          </select>
        </div>
      </form>
    </Modal>
  )
}
