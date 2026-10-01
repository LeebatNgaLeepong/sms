import { useState, useEffect } from 'react'
import api from '../api'

const FALLBACK_BANDS = [
  { min: 98, letter: '1.00', points: 1.0, label: 'Outstanding', description: '98-100' },
  { min: 95, letter: '1.25', points: 1.25, label: 'Excellent', description: '95-97' },
  { min: 92, letter: '1.50', points: 1.5, label: 'Very Good', description: '92-94' },
  { min: 89, letter: '1.75', points: 1.75, label: 'Good', description: '89-91' },
  { min: 86, letter: '2.00', points: 2.0, label: 'Fairly Good', description: '86-88' },
  { min: 83, letter: '2.25', points: 2.25, label: 'Fair', description: '83-85' },
  { min: 80, letter: '2.50', points: 2.5, label: 'Satisfactory', description: '80-82' },
  { min: 77, letter: '2.75', points: 2.75, label: 'Needs Improvement', description: '77-79' },
  { min: 75, letter: '3.00', points: 3.0, label: 'Passing', description: '75-76' },
  { min: null, letter: '5.00', points: 5.0, label: 'Failed', description: 'Below 75' },
]

let cached = null

/**
 * The grade bands the backend will actually record, read from
 * GET /api/grades/scale/ so the UI never offers a grade the server rejects.
 */
export default function useGradeScale() {
  const [bands, setBands] = useState(cached || FALLBACK_BANDS)
  const [passingPoints, setPassingPoints] = useState(3.0)

  useEffect(() => {
    let active = true
    api
      .get('/grades/scale/')
      .then((res) => {
        if (!active) return
        const next = res.data?.bands?.length ? res.data.bands : FALLBACK_BANDS
        cached = next
        setBands(next)
        if (res.data?.passing_points !== undefined) {
          setPassingPoints(Number(res.data.passing_points))
        }
      })
      .catch(() => {
        /* keep the fallback bands */
      })
    return () => {
      active = false
    }
  }, [])

  /** The band a score falls into, or null when there is no score. */
  const bandForScore = (score) => {
    if (score === '' || score === null || score === undefined) return null
    const value = Number(score)
    if (Number.isNaN(value)) return null
    return bands.find((b) => b.min === null || value >= Number(b.min)) || null
  }

  const bandForPoints = (points) => {
    const value = Number(points)
    if (Number.isNaN(value)) return null
    return bands.find((b) => Number(b.points) === value) || null
  }

  return { bands, passingPoints, bandForScore, bandForPoints }
}