import { Fragment, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import HandledBySelect, { useExecList } from '../components/HandledBy'
import ReverseForm from '../components/ReverseForm'
import { formatDate, kwd, today } from '../format'

export default function TransfersPage() {
  const { user } = useAuth()
  const [transfers, setTransfers] = useState(null)
  const [otherExecs, setOtherExecs] = useState([])
  const [reversingId, setReversingId] = useState(null)
  const [showReversed, setShowReversed] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api('/transfers/'), api('/transfers/other-execs')])
      .then(([transferData, execData]) => {
        setTransfers(transferData)
        setOtherExecs(execData)
      })
      .catch((err) => setError(err.message))
  }, [])

  function reloadTransfers() {
    api('/transfers/')
      .then(setTransfers)
      .catch((err) => setError(err.message))
  }

  async function reverseTransfer(transfer, reason) {
    const updated = await api(`/transfers/${transfer.transfer_id}/reverse`, {
      method: 'POST',
      body: { reason },
    })
    setTransfers((current) =>
      current.map((t) => (t.transfer_id === updated.transfer_id ? updated : t))
    )
    setReversingId(null)
  }

  if (!transfers) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const reversedCount = transfers.filter((transfer) => transfer.status === 'reversed').length
  const shown = showReversed
    ? transfers
    : transfers.filter((transfer) => transfer.status !== 'reversed')

  return (
    <div className="page">
      <h1>Money Transfers</h1>

      {error && <p className="error">{error}</p>}

      <RecordTransferForm otherExecs={otherExecs} onRecorded={reloadTransfers} />

      <section className="card">
        <div className="section-header">
          <h2>Transfer history</h2>
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
          <p className="hint">No transfers to show.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Amount</th>
                  <th>Recorded by</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {shown.map((transfer) => {
                  const reversed = transfer.status === 'reversed'
                  const canReverse =
                    !reversed &&
                    (user.role === 'admin' || transfer.recorded_by_exec_id === user.exec_id)
                  const isReversing = reversingId === transfer.transfer_id

                  return (
                    <Fragment key={transfer.transfer_id}>
                      <tr className={reversed ? 'reversed' : undefined}>
                        <td>{formatDate(transfer.transferred_on)}</td>
                        <td>{transfer.from_exec_name}</td>
                        <td>{transfer.to_exec_name}</td>
                        <td className="money">{kwd(transfer.amount)}</td>
                        <td>
                          {transfer.recorded_by_name}
                          {reversed && ' (reversed)'}
                        </td>
                        <td className="row-actions">
                          {canReverse && !isReversing && (
                            <button
                              className="secondary danger-text small"
                              onClick={() => setReversingId(transfer.transfer_id)}
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
                              label={`Reason for reversing ${kwd(transfer.amount)} from ${transfer.from_exec_name} to ${transfer.to_exec_name}`}
                              confirmMessage={
                                `Reverse the transfer of ${kwd(transfer.amount)} from ${transfer.from_exec_name} to ${transfer.to_exec_name}?\n\n` +
                                'It will stay in the history, marked as reversed.'
                              }
                              buttonText="Reverse transfer"
                              onCancel={() => setReversingId(null)}
                              onReverse={(reason) => reverseTransfer(transfer, reason)}
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

/* ---------- Record a transfer ---------- */

function RecordTransferForm({ otherExecs, onRecorded }) {
  const { user } = useAuth()
  const execs = useExecList()
  const isAdmin = user.role === 'admin'

  const [fromExecId, setFromExecId] = useState('')
  const [receivedBy, setReceivedBy] = useState('')
  const [amount, setAmount] = useState('')
  const [transferredOn, setTransferredOn] = useState(today)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  // Admins can pick any approved Exec as the giver (except the receiver); everyone else picks from the other Execs
  const receiverId = receivedBy ? Number(receivedBy) : user.exec_id
  const giverOptions = isAdmin
    ? execs.filter((exec) => exec.exec_id !== receiverId)
    : otherExecs

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)

    try {
      const transfer = await api('/transfers/', {
        method: 'POST',
        body: {
          from_exec_id: Number(fromExecId),
          to_exec_id: receivedBy ? Number(receivedBy) : null,
          amount,
          transferred_on: transferredOn,
        },
      })

      setMessage(
        `Recorded ${kwd(transfer.amount)} from ${transfer.from_exec_name} to ${transfer.to_exec_name}.`
      )
      onRecorded()

      setFromExecId('')
      setReceivedBy('')
      setAmount('')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card highlight-card" onSubmit={handleSubmit}>
      <h2>{isAdmin ? 'Record a money handover' : 'Record money you received'}</h2>
      <p className="hint">
        {isAdmin
          ? 'When club money is handed from one Exec to another, record it here. Leave "Received by" as "Me" if you received it.'
          : 'When another Exec hands you club money, record it here.'}
      </p>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      {giverOptions.length === 0 ? (
        <p className="hint">There are no other Execs yet.</p>
      ) : (
        <>
          <div className="form-row">
            <label>
              Received from
              <select
                value={fromExecId}
                onChange={(event) => setFromExecId(event.target.value)}
                required
              >
                <option value="">Choose an Exec</option>
                {giverOptions.map((exec) => (
                  <option key={exec.exec_id} value={exec.exec_id}>
                    {`${exec.name}${exec.is_active === false ? ' (inactive)' : ''}`}
                  </option>
                ))}
              </select>
            </label>

            {/* Admins only: record a handover that another Exec received */}
            <HandledBySelect
              label="Received by"
              execs={execs}
              value={receivedBy}
              onChange={setReceivedBy}
              exclude={fromExecId ? Number(fromExecId) : null}
            />

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
              Date
              <input
                type="date"
                value={transferredOn}
                max={today()}
                onChange={(event) => setTransferredOn(event.target.value)}
                required
              />
            </label>
          </div>

          <button type="submit" className="button-large" disabled={saving}>
            {saving ? 'Saving...' : 'Record transfer'}
          </button>
        </>
      )}
    </form>
  )
}