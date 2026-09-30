import useTerms from '../hooks/useTerms'

/**
 * Semester and school year pickers. Used anywhere a term is chosen so the
 * options always match what the backend accepts.
 */
export default function TermFields({ semester, schoolYear, onChange, idPrefix = 'term', showNote = true }) {
  const { semesters, school_years, current } = useTerms()

  return (
    <div className="form-row">
      <div className="form-group">
        <label className="form-label" htmlFor={`${idPrefix}-semester`}>
          Semester
        </label>
        <select
          id={`${idPrefix}-semester`}
          className="form-select"
          value={semester || current.semester}
          onChange={(e) => onChange({ semester: e.target.value, schoolYear })}
        >
          {semesters.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label className="form-label" htmlFor={`${idPrefix}-year`}>
          School Year
        </label>
        <select
          id={`${idPrefix}-year`}
          className="form-select"
          value={schoolYear || current.school_year}
          onChange={(e) => onChange({ semester, schoolYear: e.target.value })}
        >
          {school_years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>
      {showNote && (
        <p className="form-hint" style={{ gridColumn: '1 / -1' }}>
          Classes and enrollment for this term are scheduled together.
        </p>
      )}
    </div>
  )
}
