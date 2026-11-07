import { useEffect, useState } from 'react'
import { api } from '../../api'
import PlayerPicker from '../../components/PlayerPicker'
import { currentMonth, formatTimestamp, kwd, monthLabel } from '../../format'

function fetchHistory() {
  return api('/audit-logs/', { params: { table_name: 'fee_adjustments', limit: 50 } })
}

function describeChange(amountChange) {
  return amountChange.startsWith('-')
    ? `Reduced by ${kwd(amountChange.slice(1))}`
    : `Added ${kwd(amountChange)}`
}

export default function FeeAdjustmentsPage() {
  const [players, setPlayers] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api('/players/'), fetchHistory()])
      .then(([playerData, historyData]) => {
        setPlayers(playerData)
        setHistory(historyData)
      })
      .catch((err) => setError(err.message))
  }, [])

  function reloadHistory() {
    fetchHistory()
      .then(setHistory)
      .catch((err) => setError(err.message))
  }

  if (!players) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const playerNames = new Map(players.map((player) => [player.player_id, player.name]))

  return (
    <>
       <p className="warning">
        ⚠️ Only for exceptions agreed by the committee. Normal fees are worked out
        automatically from attendance. Every change is recorded.
      </p>

      <AdjustmentForm players={players} onSaved={reloadHistory} />
    
      <section className="card">
        <h2>Recent adjustments</h2>

        {error && <p className="error">{error}</p>}

        {history.length === 0 ? (
          <p className="hint">No fee adjustments yet.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Player</th>
                  <th>Month</th>
                  <th>Change</th>
                  <th>Reason</th>
                  <th>By</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.audit_id}>
                    <td>{formatTimestamp(entry.created_at)}</td>
                    <td>{playerNames.get(entry.new_values.player_id)}</td>
                    <td>{monthLabel(entry.new_values.fee_month)}</td>
                    <td className="money">{describeChange(entry.new_values.amount_change)}</td>
                    <td>{entry.new_values.reason}</td>
                    <td>{entry.exec_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}

function AdjustmentForm({ players, onSaved }) {
  const [playerId, setPlayerId] = useState(null)
  const [month, setMonth] = useState(currentMonth)
  const [kind, setKind] = useState('reduce')
  const [amount, setAmount] = useState('5.000')
  const [reason, setReason] = useState('')
  const [playerFees, setPlayerFees] = useState(null)
  const [reloadCount, setReloadCount] = useState(0)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  // Load the chosen player's fees, to show the current fee for the chosen month
  useEffect(() => {
    if (!playerId) {
      return
    }

    let ignore = false

    api(`/fees/players/${playerId}`)
      .then((fees) => {
        if (!ignore) setPlayerFees({ playerId, fees })
      })
      .catch(() => {})

    return () => {
      ignore = true
    }
  }, [playerId, reloadCount])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    if (!playerId) {
      setError('Choose a player first.')
      return
    }

    setSaving(true)

    try {
      const result = await api('/fees/adjustments', {
        method: 'POST',
        body: {
          player_id: playerId,
          fee_month: `${month}-01`,
          amount_change: kind === 'reduce' ? `-${amount}` : amount,
          reason,
        },
      })

      setMessage(
        `${result.player_name}'s fee for ${monthLabel(result.fee_month)} is now ${kwd(result.amount_due)}.`
      )
      setReason('')
      setReloadCount((count) => count + 1)
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const feesLoaded = playerId && playerFees?.playerId === playerId
  const monthFee = feesLoaded
    ? playerFees.fees.find((fee) => fee.fee_month === `${month}-01`)
    : null

  return (
    <form className="card highlight-card" onSubmit={handleSubmit}>
      <h2>Adjust a fee</h2>
      <p className="hint">Reduce, waive or add to one player's fee for one month. A reason is required.</p>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <div className="field">
        <span>Player</span>
        <PlayerPicker
          players={players}
          value={playerId}
          onChange={(id) => {
            setPlayerId(id)
            setMessage('')
          }}
        />
      </div>

      <label>
        Month
        <input
          type="month"
          value={month}
          onChange={(event) => event.target.value && setMonth(event.target.value)}
          required
        />
      </label>

      {feesLoaded && (
        <p className="notice">
          {monthFee
            ? `Current fee for ${monthLabel(monthFee.fee_month)}: ${kwd(monthFee.amount_due)}`
            : `No fee for ${monthLabel(`${month}-01`)}. This player didn't attend that month.`}
        </p>
      )}

      <div className="choice-row">
        <label className="checkbox">
          <input
            type="radio"
            name="kind"
            value="reduce"
            checked={kind === 'reduce'}
            onChange={() => setKind('reduce')}
          />
          Reduce / waive
        </label>
        <label className="checkbox">
          <input
            type="radio"
            name="kind"
            value="add"
            checked={kind === 'add'}
            onChange={() => setKind('add')}
          />
          Add a charge
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

      <label>
        Reason
        <input
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          maxLength={500}
          placeholder="e.g. Sibling discount agreed by the committee"
          required
        />
      </label>

      <button type="submit" className="button-large" disabled={saving}>
        {saving ? 'Saving...' : 'Save adjustment'}
      </button>
    </form>
  )
}