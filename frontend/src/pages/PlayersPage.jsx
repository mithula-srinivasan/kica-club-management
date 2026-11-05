import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import PlayerDetailsFields, {
  formValues,
  hasDemoDetails,
  requestBody,
} from '../components/PlayerDetailsFields'

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

  // Filter in the browser: the whole list is small, so this is instant as you type.
  // Spaces are ignored, so "50000000" finds "+965 5000 0000".
  const term = search.toLowerCase().replace(/\s/g, '')

  function matches(text) {
    return (text ?? '').toLowerCase().replace(/\s/g, '').includes(term)
  }

  // Ticked: only inactive players. Unticked: only active players.
  const shown = players.filter((player) => {
    if (player.is_active === showInactive) {
      return false
    }

    return (
      matches(player.name) ||
      matches(player.kica_id) ||
      matches(player.parent_name) ||
      matches(player.phone_1)
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
            placeholder="Search by name, KICA ID, parent or phone"
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
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>KICA ID</th>
                  <th>Parent</th>
                  <th>WhatsApp</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((player) => (
                  <tr key={player.player_id}>
                    <td>
                      <Link to={`/exec/players/${player.player_id}`}>{player.name}</Link>
                      {hasDemoDetails(player) && (
                        <>
                          {' '}
                          <span className="badge muted-badge">Update details</span>
                        </>
                      )}
                    </td>
                    <td>{player.kica_id}</td>
                    <td>{player.parent_name}</td>
                    <td>{player.phone_1}</td>
                    <td>
                      {player.is_active ? 'Active' : <span className="muted">Inactive</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="hint">Showing {shown.length} of {players.length} players</p>
      </section>
    </div>
  )
}
function AddPlayerForm({ onCancel }) {
  const navigate = useNavigate()
  const [values, setValues] = useState(() => formValues())
  const [nextKicaId, setNextKicaId] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Ask the backend which KICA ID this player will get
  useEffect(() => {
    api('/players/next-kica-id')
      .then((data) => setNextKicaId(data.kica_id))
      .catch((err) => setError(err.message))
  }, [])

  // Change one field, keep the others
  function setField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const player = await api('/players/', {
        method: 'POST',
        body: requestBody(values),
      })
      navigate(`/exec/players/${player.player_id}`)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Add a player</h2>

      {error && <p className="error">{error}</p>}

      <PlayerDetailsFields
        values={values}
        onChange={setField}
        isNew
        kicaId={nextKicaId}
      />

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