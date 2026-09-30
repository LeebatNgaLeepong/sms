import { useState, useEffect } from 'react'
import api from '../api'

// Cached across the app so term options are fetched once, not per page.
let cached = null
let inflight = null

const FALLBACK = {
  semesters: ['1st Sem', '2nd Sem', 'Summer'],
  school_years: ['2024-2025', '2025-2026', '2026-2027', '2027-2028'],
  current: { semester: '1st Sem', school_year: '2025-2026' },
}

const fetchTerms = () => {
  if (cached) return Promise.resolve(cached)
  if (!inflight) {
    inflight = api
      .get('/terms/')
      .then((res) => {
        cached = res.data || FALLBACK
        return cached
      })
      .catch(() => FALLBACK)
      .finally(() => {
        inflight = null
      })
  }
  return inflight
}

/**
 * Semester and school year options from the API, plus the current term.
 * Returns { semesters, school_years, current, termLabel }.
 */
export default function useTerms() {
  const [terms, setTerms] = useState(cached || FALLBACK)

  useEffect(() => {
    let active = true
    fetchTerms().then((data) => {
      if (active) setTerms(data)
    })
    return () => {
      active = false
    }
  }, [])

  return {
    ...terms,
    termLabel: `${terms.current.semester} · ${terms.current.school_year}`,
  }
}
