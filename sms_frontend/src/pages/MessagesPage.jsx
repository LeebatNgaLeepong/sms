import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'
import { IconSearch, IconPlus, IconSend, IconBack } from '../components/Icons'

function formatTime(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function MessagesPage() {
  const { user, isStudent, isAdmin, isTeacher } = useAuth()
  const { addToast } = useToast()

  const [threads, setThreads] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingThread, setLoadingThread] = useState(false)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [search, setSearch] = useState('')

  const [showNew, setShowNew] = useState(false)
  const [counterparts, setCounterparts] = useState([])
  const [counterpartId, setCounterpartId] = useState('')
  const [startingThread, setStartingThread] = useState(false)

  const bottomRef = useRef(null)
  const active = threads.find((t) => t.id === activeId) || null

  const fetchThreads = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/threads/', { params: { page_size: 100 } })
      setThreads(res.data.results || res.data || [])
    } catch (err) {
      console.error('Threads fetch error:', err)
      addToast('Failed to load messages', 'error')
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    fetchThreads()
  }, [fetchThreads])

  const openThread = useCallback(async (id) => {
    setActiveId(id)
    setLoadingThread(true)
    setMessages([])
    try {
      const res = await api.get(`/threads/${id}/messages/`)
      setMessages(res.data.messages || [])
      // Refresh the list so the unread badge clears.
      fetchThreads()
    } catch (err) {
      addToast('Could not open that conversation', 'error')
      setActiveId(null)
    } finally {
      setLoadingThread(false)
    }
  }, [fetchThreads, addToast])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeId])

  const sendMessage = async (e) => {
    e?.preventDefault()
    const body = draft.trim()
    if (!body || !activeId) return
    setSending(true)
    try {
      const res = await api.post(`/threads/${activeId}/messages/`, { body })
      setMessages((prev) => [...prev, res.data])
      setDraft('')
      fetchThreads()
    } catch (err) {
      addToast(err.response?.data?.body?.[0] || 'Message not sent', 'error')
    } finally {
      setSending(false)
    }
  }

  // Who can this user start a conversation with?
  const openNew = async () => {
    setShowNew(true)
    setCounterpartId('')
    try {
      if (isStudent) {
        const res = await api.get('/teachers/')
        setCounterparts((res.data || []).map((t) => ({
          id: t.id,
          label: t.first_name ? `${t.first_name} ${t.last_name}` : t.username,
        })))
      } else if (isTeacher) {
        const res = await api.get('/students/', { params: { page_size: 300 } })
        setCounterparts((res.data.results || []).map((s) => ({
          id: s.id,
          label: `${s.name} (${s.id})`,
        })))
      }
    } catch (err) {
      console.error('Counterpart fetch error:', err)
    }
  }

  const startThread = async () => {
    if (!counterpartId) {
      addToast('Choose someone first', 'error')
      return
    }
    setStartingThread(true)
    try {
      const res = await api.post('/threads/', {
        counterpart: isStudent ? parseInt(counterpartId, 10) : counterpartId,
      })
      setShowNew(false)
      await fetchThreads()
      openThread(res.data.id)
    } catch (err) {
      addToast(err.response?.data?.counterpart?.[0] || 'Could not start conversation', 'error')
    } finally {
      setStartingThread(false)
    }
  }

  const visible = threads.filter((t) => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      t.counterpart_name.toLowerCase().includes(q) ||
      (t.subject_code || '').toLowerCase().includes(q)
    )
  })

  if (isAdmin) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1 className="page-title">Messages</h1>
            <p className="page-subtitle">Conversations between students and teachers</p>
          </div>
        </div>
        <div className="table-container">
          <div className="table-empty">
            Admins can read conversations but do not take part in them. Sign in as a
            student or a teacher to message.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Messages</h1>
          <p className="page-subtitle">
            {isStudent
              ? 'Talk to your teachers about your subjects'
              : 'Conversations with your students'}
          </p>
        </div>
        <button className="btn btn-primary" onClick={openNew} id="new-message-btn">
          <IconPlus /> New Message
        </button>
      </div>

      <div className="messenger">
        <aside className="thread-list">
          <div className="thread-list-search">
            <IconSearch />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              id="thread-search"
            />
          </div>

          {loading ? (
            <div className="thread-list-empty"><span className="spinner" /></div>
          ) : visible.length === 0 ? (
            <div className="thread-list-empty">
              {threads.length === 0 ? 'No conversations yet.' : 'No matches.'}
            </div>
          ) : (
            visible.map((t) => (
              <button
                key={t.id}
                className={`thread-item ${t.id === activeId ? 'active' : ''}`}
                onClick={() => openThread(t.id)}
                id={`thread-${t.id}`}
              >
                <div className="thread-item-top">
                  <span className="thread-item-name">{t.counterpart_name}</span>
                  {t.unread_count > 0 && (
                    <span className="thread-unread">{t.unread_count}</span>
                  )}
                </div>
                <div className="thread-item-subject">
                  {t.subject_code ? `${t.subject_code} · ` : ''}
                  {t.counterpart_role === 'teacher'
                    ? `${t.student_name} (${t.student_id})`
                    : 'your teacher'}
                </div>
                <div className="thread-item-preview">
                  {t.last_message ? t.last_message.body : 'No messages yet'}
                </div>
                <div className="thread-item-time">
                  {formatTime(t.last_message_at || t.created_at)}
                </div>
              </button>
            ))
          )}
        </aside>

        <section className="thread-panel">
          {!active ? (
            <div className="thread-empty">
              <p>Select a conversation to read it.</p>
            </div>
          ) : (
            <>
              <header className="thread-header">
                <button
                  className="btn-icon btn-ghost thread-back"
                  onClick={() => setActiveId(null)}
                  title="Back to list"
                >
                  <IconBack />
                </button>
                <div>
                  <div className="thread-header-name">{active.counterpart_name}</div>
                  <div className="thread-header-sub">
                    {active.subject_code ? `${active.subject_code} · ` : ''}
                    {active.counterpart_role}
                  </div>
                </div>
              </header>

              <div className="thread-messages">
                {loadingThread ? (
                  <div className="thread-empty"><span className="spinner" /></div>
                ) : messages.length === 0 ? (
                  <div className="thread-empty">No messages yet. Say hello.</div>
                ) : (
                  messages.map((m) => (
                    <div
                      key={m.id}
                      className={`bubble-row ${m.sender === user?.id ? 'mine' : 'theirs'}`}
                    >
                      <div className="bubble">
                        <div className="bubble-body">{m.body}</div>
                        <div className="bubble-time">{formatTime(m.created_at)}</div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={bottomRef} />
              </div>

              <form className="thread-composer" onSubmit={sendMessage}>
                <input
                  className="form-input"
                  placeholder="Write a message..."
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  maxLength={5000}
                  id="message-input"
                />
                <button
                  className="btn btn-primary"
                  type="submit"
                  disabled={sending || !draft.trim()}
                  id="send-message-btn"
                >
                  {sending ? <span className="spinner" /> : <IconSend />} Send
                </button>
              </form>
            </>
          )}
        </section>
      </div>

      {showNew && (
        <Modal
          title={isStudent ? 'Message a teacher' : 'Message a student'}
          onClose={() => setShowNew(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowNew(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={startThread}
                disabled={startingThread}
                id="start-thread-btn"
              >
                {startingThread ? <span className="spinner" /> : 'Open conversation'}
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="counterpart">
              {isStudent ? 'Teacher' : 'Student'}
            </label>
            <select
              id="counterpart"
              className="form-select"
              value={counterpartId}
              onChange={(e) => setCounterpartId(e.target.value)}
            >
              <option value="">Choose...</option>
              {counterparts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
            <p className="form-hint">
              If you already have a conversation, it opens instead of starting a new one.
            </p>
          </div>
        </Modal>
      )}
    </div>
  )
}