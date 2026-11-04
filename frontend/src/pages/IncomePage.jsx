import { Fragment, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import HandledBySelect, { useExecList } from '../components/HandledBy'
import ReverseForm from '../components/ReverseForm'
import { formatDate, kwd, today } from '../format'

export default function IncomePage() {
  const { user } = useAuth()
  const [entries, setEntries] = useState(null)
  const [reversingId, setReversingId] = useState(null)
  const [showReversed, setShowReversed] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/income/')
      .then(setEntries)
      .catch((err) => setError(err.message))
  }, [])

  function reloadIncome() {
    api('/income/')
      .then(setEntries)
      .catch((err) => setError(err.message))
  }

  async function reverseIncome(entry, reason) {
    const updated = await api(`/income/${entry.income_id}/reverse`, {
      method: 'POST',
      body: { reason },
    })
    setEntries((current) =>
      current.map((i) => (i.income_id === updated.income_id ? updated : i))
    )
    setReversingId(null)
  }

  if (!entries) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const reversedCount = entries.filter((entry) => entry.status === 'reversed').length
  const shown = showReversed
    ? entries
    : entries.filter((entry) => entry.status !== 'reversed')

  return (
    <div className="page">
      <h1>Income</h1>

      {error && <p className="error">{error}</p>}

      <RecordIncomeForm onRecorded={reloadIncome} />

      <section className="card">
        <div className="section-header">
          <h2>Income history</h2>
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

        {shown.length === 0 ? (
          <p className="hint">No income to show.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Received by</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {shown.map((entry) => {
                  const reversed = entry.status === 'reversed'
                  const canReverse =
                    !reversed &&
                    (user.role === 'admin' || entry.recorded_by_exec_id === user.exec_id)
                  const isReversing = reversingId === entry.income_id

                  return (
                    <Fragment key={entry.income_id}>
                      <tr className={reversed ? 'reversed' : undefined}>
                        <td>{formatDate(entry.income_date)}</td>
                        <td>{entry.description}</td>
                        <td className="money">{kwd(entry.amount)}</td>
                        <td>
                          {entry.received_by_name}
                          {entry.recorded_by_exec_id !== entry.received_by_exec_id && (
                            <span className="muted"> · recorded by {entry.recorded_by_name}</span>
                          )}
                          {reversed && ' (reversed)'}
                        </td>
                        <td className="row-actions">
                          {canReverse && !isReversing && (
                            <button
                              className="secondary danger-text small"
                              onClick={() => setReversingId(entry.income_id)}
                            >
                              Reverse
                            </button>
                          )}
                        </td>
                      </tr>

                      {isReversing && (
                        <tr className="reverse-row">
                          <td colSpan={5}>
                            <ReverseForm
                              label={`Reason for reversing "${entry.description}" (${kwd(entry.amount)})`}
                              confirmMessage={
                                `Reverse the income "${entry.description}" of ${kwd(entry.amount)}?\n\n` +
                                'It will stay in the history, marked as reversed, and no longer count as money received.'
                              }
                              buttonText="Reverse income"
                              onCancel={() => setReversingId(null)}
                              onReverse={(reason) => reverseIncome(entry, reason)}
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
      </section>
    </div>
  )
}

/* ---------- Record income ---------- */

function RecordIncomeForm({ onRecorded }) {
  const execs = useExecList()
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [incomeDate, setIncomeDate] = useState(today)
  const [receivedBy, setReceivedBy] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)

    try {
      const entry = await api('/income/', {
        method: 'POST',
        body: {
          description,
          amount,
          income_date: incomeDate,
          received_by_exec_id: receivedBy ? Number(receivedBy) : null,
        },
      })

      setMessage(
        entry.received_by_exec_id === entry.recorded_by_exec_id
          ? `Recorded ${kwd(entry.amount)}: ${entry.description}.`
          : `Recorded ${kwd(entry.amount)}: ${entry.description}, received by ${entry.received_by_name}.`
      )
      onRecorded()

      setDescription('')
      setAmount('')
      setReceivedBy('')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card highlight-card" onSubmit={handleSubmit}>
      <h2>Record income</h2>
      <p className="hint">
        Money the club earned, other than membership fees: for example tournament entry fees or
        equipment rental.
      </p>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <label>
        What was it for?
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          maxLength={500}
          placeholder="e.g. Rapid tournament – entry fees"
          required
        />
      </label>

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
          Date received
          <input
            type="date"
            value={incomeDate}
            max={today()}
            onChange={(event) => setIncomeDate(event.target.value)}
            required
          />
        </label>

        {/* Admins only: record income that another Exec received */}
        <HandledBySelect
          label="Received by"
          execs={execs}
          value={receivedBy}
          onChange={setReceivedBy}
        />
      </div>

      <button type="submit" className="button-large green" disabled={saving}>
        {saving ? 'Saving...' : 'Record income'}
      </button>
    </form>
  )
}