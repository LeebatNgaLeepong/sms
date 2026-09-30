/**
 * University of Antique grading helpers (1.00 - 5.00 scale).
 * Lower values are better; 3.00 is the passing mark, 5.00 is a fail.
 */

export const GRADE_POINT_ORDER = [
  '1.00',
  '1.25',
  '1.50',
  '1.75',
  '2.00',
  '2.25',
  '2.50',
  '2.75',
  '3.00',
  '4.00',
  '5.00',
]

export const GRADE_DESCRIPTIONS = {
  '1.00': 'Outstanding (98-100)',
  '1.25': 'Excellent (95-97)',
  '1.50': 'Very Good (92-94)',
  '1.75': 'Good (89-91)',
  '2.00': 'Fairly Good (86-88)',
  '2.25': 'Fair (83-85)',
  '2.50': 'Satisfactory (80-82)',
  '2.75': 'Needs Improvement (77-79)',
  '3.00': 'Passing (75-76)',
  '4.00': 'Incomplete (INC)',
  '5.00': 'Failed (below 75)',
}

const BADGE_BY_GRADE_POINT = {
  '1.00': 'badge-gp-1',
  '1.25': 'badge-gp-1',
  '1.50': 'badge-gp-2',
  '1.75': 'badge-gp-2',
  '2.00': 'badge-gp-3',
  '2.25': 'badge-gp-3',
  '2.50': 'badge-gp-4',
  '2.75': 'badge-gp-4',
  '3.00': 'badge-gp-3',
  '4.00': 'badge-gp-inc',
  '5.00': 'badge-gp-fail',
}

const COLOR_BY_GRADE_POINT = {
  '1.00': 'var(--color-success)',
  '1.25': 'var(--color-success)',
  '1.50': 'var(--color-info)',
  '1.75': 'var(--color-info)',
  '2.00': 'var(--color-gold-600)',
  '2.25': 'var(--color-gold-600)',
  '2.50': 'var(--color-warning)',
  '2.75': 'var(--color-warning)',
  '3.00': 'var(--color-warning)',
  '4.00': 'var(--color-gray-500)',
  '5.00': 'var(--color-error)',
}

const normalize = (value) => {
  if (value === null || value === undefined) return ''
  return Number.parseFloat(String(value)).toFixed(2)
}

export const gradeBadgeClass = (value) => `badge ${BADGE_BY_GRADE_POINT[normalize(value)] || 'badge-gp-inc'}`

export const gradeColor = (value) => COLOR_BY_GRADE_POINT[normalize(value)] || 'var(--color-gray-500)'

export const gradeDescription = (value) => GRADE_DESCRIPTIONS[normalize(value)] || ''

/** Colour for a GPA or GWA on the 1.00-5.00 scale (lower is better). */
export const gpaColor = (value) => {
  const num = Number.parseFloat(value)
  if (Number.isNaN(num)) return 'var(--color-gray-500)'
  if (num <= 1.5) return 'var(--color-success)'
  if (num <= 2.0) return 'var(--color-info)'
  if (num <= 2.5) return 'var(--color-gold-600)'
  if (num <= 3.0) return 'var(--color-warning)'
  return 'var(--color-error)'
}

export const gwaColor = gpaColor
