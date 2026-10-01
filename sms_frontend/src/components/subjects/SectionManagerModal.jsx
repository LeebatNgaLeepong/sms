import Modal from '../Modal'
import { IconPlus } from '../Icons'

export default function SectionManagerModal({
  isOpen,
  onClose,
  subject,
  sections,
  sectionForm,
  setSectionForm,
  teachers,
  isAdmin,
  onAddSection,
  onDeleteSection,
  savingSection,
}) {
  if (!isOpen || !subject) return null

  return (
    <Modal
      title={`Sections of ${subject.code}`}
      onClose={onClose}
      onCancel={onClose}
      formId={isAdmin ? 'add-section-form' : undefined}
      saving={savingSection}
    >
      <p className="form-hint" style={{ marginBottom: 'var(--space-4)' }}>
        A section is one class group of this subject. Each section meets at its own
        time, so you can run several at once.
      </p>

      <div className="chip-list" style={{ marginBottom: 'var(--space-4)' }}>
        {sections.length === 0 ? (
          <span style={{ color: 'var(--color-gray-500)', fontSize: 'var(--font-sm)' }}>
            No sections yet.
          </span>
        ) : (
          sections.map((s) => (
            <span key={s.id} className="chip">
              {subject.code}-{s.code} · {s.enrolled_count}/{s.capacity}
              {isAdmin && (
                <button
                  type="button"
                  className="chip-remove"
                  title={`Delete section ${s.code}`}
                  onClick={() => onDeleteSection(s)}
                >
                  &times;
                </button>
              )}
            </span>
          ))
        )}
      </div>

      {isAdmin && (
        <form onSubmit={onAddSection} className="form-row" id="add-section-form">
          <div className="form-group">
            <label className="form-label" htmlFor="section-code">
              New section code
            </label>
            <input
              id="section-code"
              className="form-input"
              value={sectionForm.code}
              onChange={(e) => setSectionForm({ ...sectionForm, code: e.target.value })}
              placeholder="A"
              maxLength={20}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="section-capacity">
              Capacity
            </label>
            <input
              id="section-capacity"
              className="form-input"
              type="number"
              min="1"
              max="500"
              value={sectionForm.capacity}
              onChange={(e) => setSectionForm({ ...sectionForm, capacity: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="section-instructor">
              Instructor
            </label>
            <select
              id="section-instructor"
              className="form-select"
              value={sectionForm.instructor}
              onChange={(e) => setSectionForm({ ...sectionForm, instructor: e.target.value })}
            >
              <option value="">Unassigned</option>
              {teachers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.first_name ? `${t.first_name} ${t.last_name}` : t.username}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <span className="form-hint">
              Fill in a code and press the green button to add a section.
            </span>
          </div>
        </form>
      )}
    </Modal>
  )
}
