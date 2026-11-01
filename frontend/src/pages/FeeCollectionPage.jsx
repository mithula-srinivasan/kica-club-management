import { Fragment, useEffect, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import PlayerPicker from '../components/PlayerPicker'
import { currentMonth, formatDate, kwd, methodLabel, monthLabel, today } from '../format'
import ReverseForm from '../components/ReverseForm'

const USUAL_FEE = '5.000'
const RECENT_LIMIT = 50

function newFormKey() {
  return crypto.randomUUID()
}

export default function FeeCollectionPage() {
  const { user } = useAuth()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [players, setPlayers] = useState(null)
  const [payments, setPayments] = useState([])
  const [refreshCount, setRefreshCount] = useState(0)
  const [error, setError] = useState('')

  // /fees?player=12 chooses that player in the payment form
  const initialPlayerId = Number(searchParams.get('player')) || null

  useEffect(() => {
    Promise.all([api('/players/'), api('/payments/')])
      .then(([playerData, paymentData]) => {
        setPlayers(playerData)
        setPayments(paymentData)
      })
      .catch((err) => setError(err.message))
  }, [])

  // Clicking "Record payment" on a list scrolls back up to the form
  useEffect(() => {
    if (initialPlayerId) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [location.key, initialPlayerId])

  function refreshAfterChange() {
    api('/payments/')
      .then(setPayments)
      .catch((err) => setError(err.message))
    setRefreshCount((count) => count + 1)
  }

  async function reversePayment(payment, reason) {
    const updated = await api(`/payments/${payment.payment_id}/reverse`, {
      method: 'POST',
      body: { reason },
    })
    setPayments((current) =>
      current.map((p) => (p.payment_id === updated.payment_id ? updated : p))
    )
    setRefreshCount((count) => count + 1)
  }

  if (!players) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  return (
    <div className="page">
      <h1>Fee Collection</h1>

      {error && <p className="error">{error}</p>}

      <RecordPaymentForm
        key={location.key}
        players={players}
        initialPlayerId={initialPlayerId}
        onRecorded={refreshAfterChange}
      />

      <div className="two-columns">
        <WhoOwes refreshCount={refreshCount} />
        <UnpaidForMonth refreshCount={refreshCount} />
      </div>

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
  const [showReversed, setShowReversed] = useState(false)

  const reversedCount = payments.filter((payment) => payment.status === 'reversed').length
  const visible = showReversed
    ? payments
    : payments.filter((payment) => payment.status !== 'reversed')
  const recent = visible.slice(0, RECENT_LIMIT)

  return (
    <section className="card">
      <div className="section-header">
        <h2>Recent payments</h2>
        {reversedCount > 0 && (
          <label className="checkbox">
            <input
              type="checkbox"
              checked={showReversed}
              onChange={(event) => setShowReversed(event.target.checked)}
            />
            Show reversed ({reversedCount})
          </label>
        )}
      </div>

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
                            label={`Reason for reversing ${kwd(payment.amount)} from ${payment.player_name}`}
                            confirmMessage={
                              `Reverse ${kwd(payment.amount)} from ${payment.player_name}?\n\n` +
                              'It will stay in the history, marked as reversed, and the player will owe this amount again.'
                            }
                            buttonText="Reverse payment"
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

      {visible.length > RECENT_LIMIT && (
        <p className="hint">Showing the {RECENT_LIMIT} most recent payments.</p>
      )}
    </section>
  )
}


function WhoOwes({ refreshCount }) {
  const [owing, setOwing] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    api('/dashboard/outstanding')
      .then((data) => {
        if (!ignore) setOwing(data)
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [refreshCount])

  return (
    <section className="card">
      <h2>Who owes</h2>

      {error && <p className="error">{error}</p>}

      {owing === null ? (
        <p className="hint">Loading...</p>
      ) : owing.length === 0 ? (
        <p className="hint">Nobody owes anything.</p>
      ) : (
        <OwingTable rows={owing} />
      )}
    </section>
  )
}

function UnpaidForMonth({ refreshCount }) {
  const [month, setMonth] = useState(currentMonth)
  const [unpaid, setUnpaid] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    api('/dashboard/unpaid', { params: { month: `${month}-01` } })
      .then((data) => {
        if (!ignore) {
          setUnpaid(data)
          setError('')
        }
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [month, refreshCount])

  return (
    <section className="card">
      <div className="section-header">
        <h2>Unpaid for {monthLabel(`${month}-01`)}</h2>
        <input
          type="month"
          value={month}
          onChange={(event) => event.target.value && setMonth(event.target.value)}
          aria-label="Choose month"
        />
      </div>

      {error && <p className="error">{error}</p>}

      {unpaid === null ? (
        <p className="hint">Loading...</p>
      ) : unpaid.length === 0 ? (
        <p className="hint">Everyone who attended has paid for this month.</p>
      ) : (
        <OwingTable rows={unpaid} />
      )}
    </section>
  )
}

function OwingTable({ rows }) {
  return (
    <table className="owing-table">
      <tbody>
        {rows.map((row) => (
          <tr key={row.player_id}>
            <td>
              <Link to={`/players/${row.player_id}`}>{row.player_name}</Link>
            </td>
            <td className="money">{kwd(row.outstanding)}</td>
            <td className="row-actions">
              <Link className="button small-button" to={`/fees?player=${row.player_id}`}>
                Record payment
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}