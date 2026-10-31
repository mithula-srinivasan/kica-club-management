import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { formatDay } from '../format'
import { deleteSessionQuestion } from './AttendancePage'

function presentIds(session) {
  return new Set(session.present_players.map((player) => player.player_id))
}

function sameIds(a, b) {
  return a.size === b.size && [...a].every((id) => b.has(id))
}

export default function SessionPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [session, setSession] = useState(null)
  const [players, setPlayers] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [savedIds, setSavedIds] = useState(new Set())
  const [search, setSearch] = useState('')
  const [changingDate, setChangingDate] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let ignore = false

    Promise.all([api(`/sessions/${sessionId}`), api('/players/')])
      .then(([sessionData, playerData]) => {
        if (ignore) return
        setSession(sessionData)
        setPlayers(playerData)
        setSelected(presentIds(sessionData))
        setSavedIds(presentIds(sessionData))
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [sessionId])

  function toggle(playerId) {
    setMessage('')
    setSelected((current) => {
      const next = new Set(current)

      if (next.has(playerId)) {
        next.delete(playerId)
      } else {
        next.add(playerId)
      }

      return next
    })
  }

  async function save() {
    setSaving(true)
    setError('')
    setMessage('')

    try {
      const updated = await api(`/sessions/${sessionId}/attendance`, {
        method: 'PUT',
        body: { player_ids: [...selected] },
      })
      setSession(updated)
      setSelected(presentIds(updated))
      setSavedIds(presentIds(updated))
      setMessage(`Attendance saved: ${updated.present_players.length} present.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function deleteSession() {
    if (!window.confirm(deleteSessionQuestion(session.session_date, savedIds.size))) {
      return
    }

    try {
      await api(`/sessions/${sessionId}`, { method: 'DELETE' })
      navigate('/attendance')
    } catch (err) {
      setError(err.message)
    }
  }

  if (!session) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const unsaved = !sameIds(selected, savedIds)
  const term = search.trim().toLowerCase()

  // Active players, plus anyone already ticked (for example, someone marked inactive later)
  const shown = players.filter((player) => {
    if (!player.is_active && !selected.has(player.player_id)) {
      return false
    }

    return (
      player.name.toLowerCase().includes(term) ||
      (player.kica_id ?? '').toLowerCase().includes(term)
    )
  })

  return (
    <div className="page">
      <Link to="/attendance" className="back-link">← All sessions</Link>

        <div className="header-actions">
          <span className="badge">{selected.size} present</span>
          {!changingDate && (
            <button className="secondary small" onClick={() => setChangingDate(true)}>
              Change date
            </button>
          )}
          <button className="secondary small danger-text" onClick={deleteSession}>
            Delete session
          </button>
        </div>

      {changingDate && (
        <ChangeDateForm
          session={session}
          onSaved={(updated) => {
            setSession(updated)
            setChangingDate(false)
            setMessage(`Date changed to ${formatDay(updated.session_date)}.`)
          }}
          onCancel={() => setChangingDate(false)}
        />
      )}

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <section className="card">
        <div className="toolbar">
          <input
            type="search"
            placeholder="Search by name or KICA ID"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search players"
          />
        </div>

        {shown.length === 0 ? (
          <p className="hint">No players match your search.</p>
        ) : (
          <ul className="checklist">
            {shown.map((player) => {
              const isPresent = selected.has(player.player_id)

              return (
                <li key={player.player_id}>
                  <label className={isPresent ? 'check-row checked' : 'check-row'}>
                    <input
                      type="checkbox"
                      checked={isPresent}
                      onChange={() => toggle(player.player_id)}
                    />
                    <span className="check-name">{player.name}</span>
                    <span className="muted">{player.kica_id}</span>
                  </label>
                </li>
              )
            })}
          </ul>
        )}
      </section>

     <div className="save-bar">
        <span>{unsaved ? 'You have unsaved changes' : 'All changes saved'}</span>
        <button onClick={save} disabled={saving || !unsaved}>
          {saving ? 'Saving...' : 'Save attendance'}
        </button>
      </div>
    </div>
  )
}

function ChangeDateForm({ session, onSaved, onCancel }) {
  const [newDate, setNewDate] = useState(session.session_date)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)

    try {
      const updated = await api(`/sessions/${session.session_id}`, {
        method: 'PATCH',
        body: { session_date: newDate },
      })
      onSaved(updated)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Change session date</h2>
      <p className="hint">
        Everyone ticked moves to the new date. Fees are recalculated automatically.
      </p>

      {error && <p className="error">{error}</p>}

      <div className="inline-form">
        <label>
          New date
          <input
            type="date"
            value={newDate}
            onChange={(event) => setNewDate(event.target.value)}
            required
          />
        </label>

        <div className="actions">
          <button type="submit" disabled={saving}>
            {saving ? 'Saving...' : 'Save date'}
          </button>
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>
    </form>
  )
}