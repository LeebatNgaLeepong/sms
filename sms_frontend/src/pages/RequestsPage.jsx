import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import TermFields from '../components/TermFields'
import useTerms from '../hooks/useTerms'
import { IconSearch, IconPlus, IconCheck, IconClose } from '../components/Icons'

const STATUS_BADGE = {
  pending: 'badge-pending',
  approved: 'badge-gp-1',
  rejected: 'badge-gp-fail',
}

function formatDate(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function EnrollmentRequestsPage() {
  const { isStudent, isAdmin, isTeacher } = useAuth()
  const { addToast } = useToast()
  const { current } = useTerms()

  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const [showModal, setShowModal] = useState(false)
  const [subjects, setSubjects] = useState([])
  const [saving, setSaving] = useState(false)
  const [decidingId, setDecidingId] = useState(null)
  const [form, setForm] = useState({
    subject: '',
    reason: '',
    semester: current.semester,
    school_year: current.school_year,
  })

  const canDecide = isAdmin || isTeacher

  const fetchRequests = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page_size: 200 }
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const res = await api.get('/enrollment-requests/', { params })
      setRequests(res.data.results || res.data || [])
    } catch (err) {
      console.error('Requests fetch error:', err)
      addToast('Failed to load requests', 'error')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, search, addToast])

  useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  const fetchSubjects = useCallback(async () => {
    try {
      const res = await api.get('/subjects/', { params: { page_size: 300 } })
      setSubjects(res.data.results || res.data || [])
    } catch (err) {
      console.error('Subjects fetch error:', err)
    }
  }, [])

  useEffect(() => {
    if (isStudent) fetchSubjects()
  }, [isStudent, fetchSubjects])

  // A student cannot request a subject they already take, so offer only the rest.
  const availableSubjects = isStudent && requests.length >= 0 ? subjects : subjects

  const openCreate = () => {
    setForm({
      subject: '',
      reason: '',
      semester: current.semester,
      school_year: current.school_year,
    })
    setShowModal(true)
  }

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!form.subject) {
      addToast('Choose a subject first', 'error')
      return
    }
    setSaving(true)
    try {
      await api.post('/enrollment-requests/', {
        subject: parseInt(form.subject),
        reason: form.reason,
        semester: form.semester,
        school_year: form.school_year,
      })
      addToast('Request sent. You will be notified once it is reviewed.', 'success')
      setShowModal(false)
      fetchRequests()
    } catch (err) {
      const data = err.response?.data
      let msg = 'Could not send the request'
      if (data && typeof data === 'object') {
        msg = Object.entries(data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('. ')
      }
      addToast(msg, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDecision = async (request, decision) => {
    const verb = decision === 'approved' ? 'approve' : 'reject'
    if (!window.confirm(`${verb === 'approve' ? 'Approve' : 'Reject'} ${request.subject_code} for ${request.student_name}?`)) {
      return
    }
    setDecidingId(request.id)
    try {
      const res = await api.post(`/enrollment-requests/${request.id}/decision/`, {
        decision,
        note: '',
      })
      addToast(res.data.detail || 'Request updated', 'success')
      fetchRequests()
    } catch (err) {
      addToast(err.response?.data?.detail || 'Could not update the request', 'error')
    } finally {
      setDecidingId(null)
    }
  }

  const handleWithdraw = async (request) => {
    if (!window.confirm(`Withdraw your request for ${request.subject_code}?`)) return
    try {
      await api.delete(`/enrollment-requests/${request.id}/`)
      addToast('Request withdrawn', 'success')
      fetchRequests()
    } catch {
      addToast('Could not withdraw the request', 'error')
    }
  }

  const pendingCount = requests.filter((r) => r.status === 'pending').length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Subject Requests</h1>
          <p className="page-subtitle">
            {isStudent
              ? 'Ask to add a subject to your load. Your teacher reviews it.'
              : `${pendingCount} request${pendingCount !== 1 ? 's' : ''} waiting on a decision`}
          </p>
        </div>
        {isStudent && (
          <button className="btn btn-primary" onClick={openCreate} id="new-request-btn">
            <IconPlus /> Request a Subject
          </button>
        )}
      </div>

      <div className="table-container">
        <div className="table-toolbar">
          <div className="table-search">
            <IconSearch />
            <input
              type="text"
              placeholder={isStudent ? 'Search subject...' : 'Search student or subject...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchRequests()}
              id="request-search"
            />
          </div>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            id="request-status-filter"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        {loading ? (
          <div className="loading-page"><div className="spinner spinner-lg" /></div>
        ) : requests.length === 0 ? (
          <div className="table-empty">
            {isStudent
              ? 'You have no subject requests yet.'
              : 'No requests to review.'}
          </div>
        ) : (
          <table className="data-table" id="requests-table">
            <thead>
              <tr>
                {!isStudent && <th>Student</th>}
                <th>Subject</th>
                <th>Term</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Reviewed</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  {!isStudent && (
                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--color-gray-900)' }}>
                        {r.student_name}
                      </div>
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>
                        {r.student_id}
                      </div>
                    </td>
                  )}
                  <td>
                    <div style={{ fontWeight: 500 }}>{r.subject_code}</div>
                    <div style={{ fontSize: 'var(--font-xs)', color: 'var(--color-gray-400)' }}>
                      {r.subject_name} · {r.subject_units} units
                    </div>
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>{r.term}</td>
                  <td style={{ maxWidth: 260, color: 'var(--color-gray-600)' }}>
                    {r.reason || '—'}
                  </td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[r.status] || ''}`}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ color: 'var(--color-gray-500)', fontSize: 'var(--font-xs)' }}>
                    {r.reviewed_at ? (
                      <>
                        {r.status} by {r.reviewed_by_username || 'staff'}
                        <div>{formatDate(r.reviewed_at)}</div>
                      </>
                    ) : (
                      formatDate(r.created_at)
                    )}
                  </td>
                  <td>
                    <div className="table-actions">
                      {canDecide && r.status === 'pending' && (
                        <>
                          <button
                            className="btn-icon btn-ghost"
                            title="Approve"
                            disabled={decidingId === r.id}
                            onClick={() => handleDecision(r, 'approved')}
                            id={`approve-request-${r.id}`}
                          >
                            <IconCheck />
                          </button>
                          <button
                            className="btn-icon btn-ghost"
                            title="Reject"
                            disabled={decidingId === r.id}
                            onClick={() => handleDecision(r, 'rejected')}
                            id={`reject-request-${r.id}`}
                          >
                            <IconClose />
                          </button>
                        </>
                      )}
                      {isStudent && r.status === 'pending' && (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleWithdraw(r)}
                          id={`withdraw-request-${r.id}`}
                        >
                          Withdraw
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <Modal
          title="Request a Subject"
          onClose={() => setShowModal(false)}
          onCancel={() => setShowModal(false)}
          onSave={handleSubmit}
          saving={saving}
          saveDisabled={!form.subject}
        >
          <form id="request-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="request-subject">
                Subject
              </label>
              <select
                id="request-subject"
                className="form-select"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                required
              >
                <option value="">Choose a subject</option>
                {availableSubjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} · {s.name} ({s.units} units)
                  </option>
                ))}
              </select>
            </div>

            <TermFields
              idPrefix="request"
              semester={form.semester}
              schoolYear={form.school_year}
              onChange={({ semester, schoolYear }) =>
                setForm((f) => ({ ...f, semester, school_year: schoolYear }))
              }
            />

            <div className="form-group">
              <label className="form-label" htmlFor="request-reason">
                Why do you need this subject?
              </label>
              <textarea
                id="request-reason"
                className="form-input"
                rows="3"
                maxLength="500"
                value={form.reason}
                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                placeholder="e.g. It is required for my major next semester."
              />
              <p className="form-hint">
                Your teacher for that subject reviews this. If it is approved you are
                enrolled and a class time is assigned automatically.
              </p>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}