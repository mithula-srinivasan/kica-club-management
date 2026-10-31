import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { today } from '../format'

export default function PlayersPage() {
  const [players, setPlayers] = useState(null)
  const [search, setSearch] = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/players/')
      .then(setPlayers)
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return <p className="error">{error}</p>
  }

  if (!players) {
    return <p className="loading">Loading...</p>
  }

  // Filter in the browser: the whole list is small, so this is instant as you type
  const term = search.trim().toLowerCase()
  const shown = players.filter((player) => {
    if (!showInactive && !player.is_active) {
      return false
    }

    return (
      player.name.toLowerCase().includes(term) ||
      (player.kica_id ?? '').toLowerCase().includes(term)
    )
  })

  return (
    <div className="page">
      <div className="section-header">
        <h1>Players</h1>
        {!adding && <button onClick={() => setAdding(true)}>Add player</button>}
      </div>

      {adding && <AddPlayerForm onCancel={() => setAdding(false)} />}

      <section className="card">
        <div className="toolbar">
          <input
            type="search"
            placeholder="Search by name or KICA ID"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search players"
          />
          <label className="checkbox">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(event) => setShowInactive(event.target.checked)}
            />
            Show inactive players
          </label>
        </div>

        {shown.length === 0 ? (
          <p className="hint">No players match your search.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>KICA ID</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((player) => (
                <tr key={player.player_id}>
                  <td>
                    <Link to={`/players/${player.player_id}`}>{player.name}</Link>
                  </td>
                  <td>{player.kica_id}</td>
                  <td>{player.is_active ? 'Active' : <span className="muted">Inactive</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <p className="hint">Showing {shown.length} of {players.length} players</p>
      </section>
    </div>
  )
}

function AddPlayerForm({ onCancel }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [kicaId, setKicaId] = useState('')
  const [joinedOn, setJoinedOn] = useState(today)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const player = await api('/players/', {
        method: 'POST',
        body: { name, kica_id: kicaId, joined_on: joinedOn },
      })
      navigate(`/players/${player.player_id}`)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Add a player</h2>

      {error && <p className="error">{error}</p>}

      <label>
        Full name
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>

      <label>
        KICA ID
        <input value={kicaId} onChange={(event) => setKicaId(event.target.value)} required />
      </label>

      <label>
        Joined on
        <input
          type="date"
          value={joinedOn}
          onChange={(event) => setJoinedOn(event.target.value)}
          required
        />
      </label>

      <div className="actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding...' : 'Add player'}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}