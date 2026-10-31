import { Fragment, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import PlayerPicker from '../components/PlayerPicker'
import { formatDate, kwd, methodLabel, today } from '../format'

const USUAL_FEE = '5.000'
const RECENT_LIMIT = 50

function newFormKey() {
  return crypto.randomUUID()
}

export default function FeeCollectionPage() {
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const [players, setPlayers] = useState(null)
  const [payments, setPayments] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api('/players/'), api('/payments/')])
      .then(([playerData, paymentData]) => {
        setPlayers(playerData)
        setPayments(paymentData)
      })
      .catch((err) => setError(err.message))
  }, [])

  function reloadPayments() {
    api('/payments/')
      .then(setPayments)
      .catch((err) => setError(err.message))
  }

    async function reversePayment(payment, reason) {
    const updated = await api(`/payments/${payment.payment_id}/reverse`, {
      method: 'POST',
      body: { reason },
    })
    setPayments((current) =>
      current.map((p) => (p.payment_id === updated.payment_id ? updated : p))
    )
  }

  if (!players) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  // Coming from a player's page: /fees?player=12 chooses that player straight away
  const initialPlayerId = Number(searchParams.get('player')) || null

  return (
    <div className="page">
      <h1>Fee Collection</h1>

      {error && <p className="error">{error}</p>}

      <RecordPaymentForm
        players={players}
        initialPlayerId={initialPlayerId}
        onRecorded={reloadPayments}
      />

      <RecentPayments payments={payments} user={user} onReverse={reversePayment} />
    </div>
  )
}

function RecordPaymentForm({ players, initialPlayerId, onRecorded }) {
  const [playerId, setPlayerId] = useState(initialPlayerId)
  const [statement, setStatement] = useState(null)
  const [amount, setAmount] = useState(USUAL_FEE)
  const [paidOn, setPaidOn] = useState(today)
  const [method, setMethod] = useState('cash')
  const [note, setNote] = useState('')
  const [formKey, setFormKey] = useState(newFormKey)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  // Load how much the chosen player still owes
  useEffect(() => {
    if (!playerId) {
      return
    }

    let ignore = false

    api(`/payments/players/${playerId}/statement`)
      .then((data) => {
        if (!ignore) setStatement(data)
      })
      .catch(() => {})

    return () => {
      ignore = true
    }
  }, [playerId])

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
      const payment = await api('/payments/', {
        method: 'POST',
        body: {
          player_id: playerId,
          amount,
          paid_on: paidOn,
          method,
          note: note.trim() || null,
          idempotency_key: formKey,
        },
      })

      setMessage(`Recorded ${kwd(payment.amount)} from ${payment.player_name}.`)
      onRecorded()

      // A fresh form, with a new key, for the next payment
      setPlayerId(null)
      setAmount(USUAL_FEE)
      setNote('')
      setFormKey(newFormKey())
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const showBalance = playerId && statement?.player_id === playerId

  return (
    <form className="card highlight-card" onSubmit={handleSubmit}>
      <h2>Record a payment</h2>

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

      {showBalance && (
        <p className="notice">
          Still to pay: <strong>{kwd(statement.outstanding)}</strong>
          {Number(statement.credit) > 0 && ` · Paid in advance: ${kwd(statement.credit)}`}
        </p>
      )}

      <div className="form-row">
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
          Date paid
          <input
            type="date"
            value={paidOn}
            max={today()}
            onChange={(event) => setPaidOn(event.target.value)}
            required
          />
        </label>

        <label>
          Method
          <select value={method} onChange={(event) => setMethod(event.target.value)}>
            <option value="cash">Cash</option>
            <option value="bank_transfer">Bank transfer</option>
          </select>
        </label>
      </div>

      <label>
        Note (optional)
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={500}
          placeholder="e.g. bank reference"
        />
      </label>

      <button type="submit" className="button-large" disabled={saving}>
        {saving ? 'Saving...' : 'Record payment'}
      </button>
    </form>
  )
}

function RecentPayments({ payments, user, onReverse }) {
  const [reversingId, setReversingId] = useState(null)
  const recent = payments.slice(0, RECENT_LIMIT)

  return (
    <section className="card">
      <h2>Recent payments</h2>

      {recent.length === 0 ? (
        <p className="hint">No payments recorded yet.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Player</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Collected by</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {recent.map((payment) => {
                const reversed = payment.status === 'reversed'
                const canReverse =
                  !reversed &&
                  (user.role === 'admin' || payment.recorded_by_exec_id === user.exec_id)
                const isReversing = reversingId === payment.payment_id

                return (
                  <Fragment key={payment.payment_id}>
                    <tr className={reversed ? 'reversed' : undefined}>
                      <td>{formatDate(payment.paid_on)}</td>
                      <td>
                        <Link to={`/players/${payment.player_id}`}>{payment.player_name}</Link>
                      </td>
                      <td className="money">{kwd(payment.amount)}</td>
                      <td>{methodLabel(payment.method)}</td>
                      <td>
                        {payment.recorded_by_name}
                        {reversed && ' (reversed)'}
                      </td>
                      <td className="row-actions">
                        {canReverse && !isReversing && (
                          <button
                            className="secondary danger-text small"
                            onClick={() => setReversingId(payment.payment_id)}
                          >
                            Reverse
                          </button>
                        )}
                      </td>
                    </tr>

                    {isReversing && (
                      <tr className="reverse-row">
                        <td colSpan={6}>
                          <ReverseForm
                            payment={payment}
                            onCancel={() => setReversingId(null)}
                            onReverse={async (reason) => {
                              await onReverse(payment, reason)
                              setReversingId(null)
                            }}
                          />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {payments.length > RECENT_LIMIT && (
        <p className="hint">Showing the {RECENT_LIMIT} most recent payments.</p>
      )}
    </section>
  )
}

function ReverseForm({ payment, onReverse, onCancel }) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (!reason.trim()) {
      setError('Please give a reason for reversing this payment.')
      return
    }

    const confirmed = window.confirm(
      `Reverse ${kwd(payment.amount)} from ${payment.player_name}?\n\n` +
        'It will stay in the history, marked as reversed, and the player will owe this amount again.'
    )

    if (!confirmed) {
      return
    }

    setSaving(true)

    try {
      await onReverse(reason.trim())
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <form className="reverse-form" onSubmit={handleSubmit}>
      <label>
        Reason for reversing {kwd(payment.amount)} from {payment.player_name}
        <input
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          maxLength={500}
          placeholder="e.g. entered the wrong amount"
          autoFocus
        />
      </label>

      {error && <p className="error">{error}</p>}

      <div className="actions">
        <button type="submit" className="danger" disabled={saving}>
          {saving ? 'Reversing...' : 'Reverse payment'}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}