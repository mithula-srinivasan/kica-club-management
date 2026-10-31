import { useEffect, useState } from 'react'
import { api } from '../../api'
import PlayerPicker from '../../components/PlayerPicker'
import { formatDate, kwd, today } from '../../format'

function describeBalance(amount) {
  return amount.startsWith('-') ? `Paid in advance ${kwd(amount.slice(1))}` : `Owed ${kwd(amount)}`
}

export default function OpeningBalancesPage() {
  const [asOf, setAsOf] = useState(today)
  const [openings, setOpenings] = useState(null)
  const [execs, setExecs] = useState([])
  const [players, setPlayers] = useState([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    Promise.all([api('/opening-balances/'), api('/execs/'), api('/players/')])
      .then(([openingData, execData, playerData]) => {
        setOpenings(openingData)
        setExecs(execData)
        setPlayers(playerData)
      })
      .catch((err) => setError(err.message))
  }, [])

  function done(text) {
    setError('')
    setMessage(text)
    api('/opening-balances/')
      .then(setOpenings)
      .catch((err) => setError(err.message))
  }

  function failed(err) {
    setMessage('')
    setError(err.message)
  }

  if (!openings) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const execOpenings = new Map(openings.execs.map((row) => [row.exec_id, row]))

  return (
    <>

      <p className="warning">
        ⚠️ Only for entering the starting figures once, when the app takes over from Excel.
        Do not use this for day-to-day changes. Every change is recorded.
      </p>

      <section className="card"></section>
      <section className="card">
        <h2>Opening balances</h2>
        <p className="hint">
          Enter these once, when the app takes over from the Excel sheet: how much club money
          each Exec was holding, and what each member owed or had paid in advance. Everything
          after that is recorded in the app.
        </p>

        <label className="inline-label">
          Balances as of
          <input
            type="date"
            value={asOf}
            max={today()}
            onChange={(event) => setAsOf(event.target.value)}
          />
        </label>
      </section>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <section className="card">
        <h2>Cash held by each Exec</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Exec</th>
                <th>Amount (KWD)</th>
                <th>Saved</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {execs.map((exec) => {
                const opening = execOpenings.get(exec.exec_id)

                return (
                  <ExecOpeningRow
                    key={`${exec.exec_id}-${opening?.updated_at ?? 'none'}`}
                    exec={exec}
                    opening={opening}
                    asOf={asOf}
                    onDone={done}
                    onFail={failed}
                  />
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <PlayerOpenings
        players={players}
        openings={openings.players}
        asOf={asOf}
        onDone={done}
        onFail={failed}
      />
    </>
  )
}

function ExecOpeningRow({ exec, opening, asOf, onDone, onFail }) {
  const [amount, setAmount] = useState(opening ? opening.amount : '')
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)

    try {
      await api(`/opening-balances/execs/${exec.exec_id}`, {
        method: 'PUT',
        body: { amount, as_of: asOf },
      })
      onDone(`Saved opening cash for ${exec.name}.`)
    } catch (err) {
      onFail(err)
      setSaving(false)
    }
  }

  async function remove() {
    if (!window.confirm(`Remove the opening cash for ${exec.name}?`)) {
      return
    }

    try {
      await api(`/opening-balances/execs/${exec.exec_id}`, { method: 'DELETE' })
      onDone(`Removed opening cash for ${exec.name}.`)
    } catch (err) {
      onFail(err)
    }
  }

  return (
    <tr>
      <td>
        {exec.name}
        {!exec.is_active && <span className="muted"> (inactive)</span>}
      </td>
      <td>
        <input
          className="amount-input"
          type="number"
          step="0.001"
          min="0"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          aria-label={`Opening cash for ${exec.name}`}
        />
      </td>
      <td>
        {opening ? (
          <span className="muted">as of {formatDate(opening.as_of)}</span>
        ) : (
          <span className="muted">Not set</span>
        )}
      </td>
      <td className="row-actions">
        <div className="row-buttons">
          <button className="small" onClick={save} disabled={saving || amount === ''}>
            {saving ? 'Saving...' : 'Save'}
          </button>
          {opening && (
            <button className="secondary danger-text small" onClick={remove}>
              Remove
            </button>
          )}
        </div>
      </td>
    </tr>
  )
}

function PlayerOpenings({ players, openings, asOf, onDone, onFail }) {
  const [playerId, setPlayerId] = useState(null)
  const [kind, setKind] = useState('owed')
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)

  const existing = openings.find((row) => row.player_id === playerId)

  async function save(event) {
    event.preventDefault()

    if (!playerId) {
      onFail(new Error('Choose a member first.'))
      return
    }

    setSaving(true)

    try {
      const saved = await api(`/opening-balances/players/${playerId}`, {
        method: 'PUT',
        body: {
          amount: kind === 'credit' ? `-${amount}` : amount,
          as_of: asOf,
        },
      })
      onDone(`Saved opening balance for ${saved.player_name}.`)
      setPlayerId(null)
      setAmount('')
    } catch (err) {
      onFail(err)
    } finally {
      setSaving(false)
    }
  }

  async function remove(row) {
    if (!window.confirm(`Remove the opening balance for ${row.player_name}?`)) {
      return
    }

    try {
      await api(`/opening-balances/players/${row.player_id}`, { method: 'DELETE' })
      onDone(`Removed opening balance for ${row.player_name}.`)
    } catch (err) {
      onFail(err)
    }
  }

  return (
    <section className="card">
      <h2>Member balances</h2>
      <p className="hint">
        Only members who owed money or had paid in advance. Everyone else starts at zero.
      </p>

      <form className="stacked-form" onSubmit={save}>
        <div className="field">
          <span>Member</span>
          <PlayerPicker players={players} value={playerId} onChange={setPlayerId} />
        </div>

        {existing && (
          <p className="notice">
            Currently: {describeBalance(existing.amount)}. Saving will replace it.
          </p>
        )}

        <div className="choice-row">
          <label className="checkbox">
            <input
              type="radio"
              name="opening-kind"
              checked={kind === 'owed'}
              onChange={() => setKind('owed')}
            />
            Owed money
          </label>
          <label className="checkbox">
            <input
              type="radio"
              name="opening-kind"
              checked={kind === 'credit'}
              onChange={() => setKind('credit')}
            />
            Paid in advance
          </label>
        </div>

        <label>
          Amount (KWD)
          <input
            type="number"
            step="0.001"
            min="0.001"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            required
          />
        </label>

        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save member balance'}
        </button>
      </form>

      {openings.length === 0 ? (
        <p className="hint">No member balances entered yet.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Member</th>
                <th>Balance</th>
                <th>As of</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {openings.map((row) => (
                <tr key={row.player_id}>
                  <td>{row.player_name}</td>
                  <td className="money">{describeBalance(row.amount)}</td>
                  <td>{formatDate(row.as_of)}</td>
                  <td className="row-actions">
                    <button className="secondary danger-text small" onClick={() => remove(row)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}