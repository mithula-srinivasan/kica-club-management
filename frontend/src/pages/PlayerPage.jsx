import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import Figure from '../components/Figure'
import { formatDate, kwd, monthLabel } from '../format'

export default function PlayerPage() {
  const { playerId } = useParams()
  const [player, setPlayer] = useState(null)
  const [statement, setStatement] = useState(null)
  const [payments, setPayments] = useState([])
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    Promise.all([
      api(`/players/${playerId}`),
      api(`/payments/players/${playerId}/statement`),
      api('/payments/', { params: { player_id: playerId } }),
    ])
      .then(([playerData, statementData, paymentData]) => {
        if (ignore) return
        setPlayer(playerData)
        setStatement(statementData)
        setPayments(paymentData)
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [playerId])

  async function toggleActive() {
    const question = player.is_active
      ? `Mark ${player.name} as inactive? They will be hidden from the players list, but all their history is kept.`
      : `Mark ${player.name} as active again?`

    if (!window.confirm(question)) {
      return
    }

    setError('')

    try {
      const updated = await api(`/players/${playerId}/status`, {
        method: 'PATCH',
        params: { is_active: !player.is_active },
      })
      setPlayer(updated)
    } catch (err) {
      setError(err.message)
    }
  }

  if (!player) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  return (
    <div className="page">
      <Link to="/players" className="back-link">← All players</Link>

      <div className="section-header">
        <h1>
          {player.name}
          {!player.is_active && <span className="badge muted-badge">Inactive</span>}
        </h1>
        <Link className="button" to={`/fees?player=${player.player_id}`}>
          Record payment
        </Link>
      </div>

      {error && <p className="error">{error}</p>}

      {editing ? (
        <EditPlayerForm
          player={player}
          onSaved={(updated) => {
            setPlayer(updated)
            setEditing(false)
          }}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <section className="card">
          <dl className="details">
            <div>
              <dt>KICA ID</dt>
              <dd>{player.kica_id ?? '—'}</dd>
            </div>
            <div>
              <dt>Joined</dt>
              <dd>{player.joined_on ? formatDate(player.joined_on) : '—'}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{player.is_active ? 'Active' : 'Inactive'}</dd>
            </div>
          </dl>

          <div className="actions">
            <button className="secondary" onClick={() => setEditing(true)}>
              Edit details
            </button>
            <button className="secondary" onClick={toggleActive}>
              {player.is_active ? 'Mark inactive' : 'Mark active'}
            </button>
          </div>
        </section>
      )}

      <FeeHistory statement={statement} />
      <PaymentHistory payments={payments} />
    </div>
  )
}

function EditPlayerForm({ player, onSaved, onCancel }) {
  const [name, setName] = useState(player.name)
  const [kicaId, setKicaId] = useState(player.kica_id ?? '')
  const [joinedOn, setJoinedOn] = useState(player.joined_on ?? '')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    const changes = { name, kica_id: kicaId }

    if (joinedOn) {
      changes.joined_on = joinedOn
    }

    try {
      const updated = await api(`/players/${player.player_id}`, {
        method: 'PATCH',
        body: changes,
      })
      onSaved(updated)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Edit details</h2>

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
        <input type="date" value={joinedOn} onChange={(event) => setJoinedOn(event.target.value)} />
      </label>

      <div className="actions">
        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : 'Save changes'}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

function FeeHistory({ statement }) {
  // Newest month first; the opening balance (the oldest) ends up at the bottom
  const months = [...statement.months].reverse()

  return (
    <section className="card">
      <h2>Fees</h2>

      <div className="figures">
        <Figure label="Still to pay" value={kwd(statement.outstanding)} />
        <Figure label="Paid in advance" value={kwd(statement.credit)} />
      </div>

      {months.length === 0 ? (
        <p className="hint">No fees yet. A fee appears once the player attends a session.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Month</th>
              <th className="amount">Fee</th>
              <th className="amount">Paid</th>
              <th className="amount">Still to pay</th>
            </tr>
          </thead>
          <tbody>
            {months.map((month) => (
              <tr key={month.is_opening_balance ? 'opening' : month.fee_month}>
                <td>
                  {month.is_opening_balance
                    ? `Owed from before (as of ${formatDate(month.fee_month)})`
                    : monthLabel(month.fee_month)}
                </td>
                <td className="amount">{kwd(month.amount_due)}</td>
                <td className="amount">{kwd(month.amount_paid)}</td>
                <td className="amount">
                  {Number(month.remaining) > 0 ? (
                    kwd(month.remaining)
                  ) : (
                    <span className="paid">Paid</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function PaymentHistory({ payments }) {
  return (
    <section className="card">
      <h2>Payments received</h2>

      {payments.length === 0 ? (
        <p className="hint">No payments recorded yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th className="amount">Amount</th>
              <th>Method</th>
              <th>Collected by</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr
                key={payment.payment_id}
                className={payment.status === 'reversed' ? 'reversed' : undefined}
              >
                <td>{formatDate(payment.paid_on)}</td>
                <td className="amount">{kwd(payment.amount)}</td>
                <td>{payment.method === 'bank_transfer' ? 'Bank transfer' : 'Cash'}</td>
                <td>
                  {payment.recorded_by_name}
                  {payment.status === 'reversed' && ' (reversed)'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}