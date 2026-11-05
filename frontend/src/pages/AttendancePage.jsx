import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { formatDay, today } from '../format'

export function deleteSessionQuestion(sessionDate, presentCount) {
  return (
    `Delete the session on ${formatDay(sessionDate)}?\n\n` +
    `${presentCount} players are marked present. Their attendance for this date will be removed, ` +
    'and any fees that depended on it will be recalculated. This cannot be undone.'
  )
}

export default function AttendancePage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState(null)
  const [sessionDate, setSessionDate] = useState(today)
  const [existing, setExisting] = useState(null)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    api('/sessions/')
      .then(setSessions)
      .catch((err) => setError(err.message))
  }, [])

  async function createSession(event) {
    event.preventDefault()
    setError('')
    setExisting(null)

    // A session already exists on this date: point to it rather than creating a duplicate
    const match = sessions.find((session) => session.session_date === sessionDate)

    if (match) {
      setExisting(match)
      return
    }

    setCreating(true)

    try {
      const created = await api('/sessions/', {
        method: 'POST',
        body: { session_date: sessionDate },
      })
      navigate(`/exec/attendance/${created.session_id}`)
    } catch (err) {
      setError(err.message)
      setCreating(false)
    }
  }

  async function deleteSession(session) {
    if (!window.confirm(deleteSessionQuestion(session.session_date, session.present_count))) {
      return
    }

    setError('')

    try {
      await api(`/sessions/${session.session_id}`, { method: 'DELETE' })
      setSessions((current) => current.filter((s) => s.session_id !== session.session_id))
    } catch (err) {
      setError(err.message)
    }
  }

  if (!sessions) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  return (
    <div className="page">
      <h1>Attendance</h1>

      {error && <p className="error">{error}</p>}

      <form className="card" onSubmit={createSession}>
        <h2>Create a session</h2>

        <div className="inline-form">
          <label>
            Session date
            <input
              type="date"
              value={sessionDate}
              onChange={(event) => {
                setSessionDate(event.target.value)
                setExisting(null)
              }}
              required
            />
          </label>
          <button type="submit" disabled={creating}>
            {creating ? 'Creating...' : 'Create session'}
          </button>
        </div>

        {existing && (
          <p className="notice">
            A session already exists on {formatDay(existing.session_date)}.{' '}
            <Link to={`/exec/attendance/${existing.session_id}`}>Open it</Link>
          </p>
        )}
      </form>

      <section className="card">
        <h2>Past sessions</h2>

        {sessions.length === 0 ? (
          <p className="hint">No sessions yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th className="amount">Present</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.session_id}>
                  <td>
                    <Link to={`/exec/attendance/${session.session_id}`}>
                      {formatDay(session.session_date)}
                    </Link>
                  </td>
                  <td className="amount">{session.present_count}</td>
                  <td className="row-actions">
                    <button
                      className="secondary danger-text small"
                      onClick={() => deleteSession(session)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}