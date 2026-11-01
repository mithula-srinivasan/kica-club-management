import { useEffect, useState } from 'react'
import { api } from '../../api'
import { currentMonth, kwd, monthLabel } from '../../format'

// The original rate is dated 2000-01-01, meaning "since before the app existed"
function startLabel(effectiveFrom) {
  return effectiveFrom === '2000-01-01' ? 'From the start' : `From ${monthLabel(effectiveFrom)}`
}

export default function FeeRatePage() {
  const [rates, setRates] = useState(null)
  const [amount, setAmount] = useState('')
  const [month, setMonth] = useState(currentMonth)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api('/fees/rates')
      .then(setRates)
      .catch((err) => setError(err.message))
  }, [])

  function reloadRates() {
    api('/fees/rates')
      .then(setRates)
      .catch((err) => setError(err.message))
  }

  async function addRate(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    const startLabelText = monthLabel(`${month}-01`)

    if (
      !window.confirm(
        `Set the monthly fee to ${kwd(amount)} from ${startLabelText}?\n\n` +
          'Every member is charged this from that month onwards. Earlier months keep their current rate.'
      )
    ) {
      return
    }

    setSaving(true)

    try {
      await api('/fees/rates', {
        method: 'POST',
        body: { monthly_amount: amount, effective_from: `${month}-01` },
      })
      setMessage(`The monthly fee will be ${kwd(amount)} from ${startLabelText}.`)
      setAmount('')
      reloadRates()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function removeRate(rate) {
    if (!window.confirm(`Remove the upcoming rate of ${kwd(rate.monthly_amount)} ${startLabel(rate.effective_from).toLowerCase()}?`)) {
      return
    }

    setError('')
    setMessage('')

    try {
      await api(`/fees/rates/${rate.fee_rate_id}`, { method: 'DELETE' })
      setMessage('The upcoming rate was removed.')
      reloadRates()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!rates) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  const thisMonth = `${currentMonth()}-01`

  // Rates are newest first, so the first one that has already started is the current rate
  const current = rates.find((rate) => rate.effective_from <= thisMonth)

  return (
    <>
      <p className="warning">
        ⚠️ Changing the fee affects every member from the chosen month onwards. Only change it
        when the committee has agreed. Every change is recorded.
      </p>

      <section className="card">
        <h2>Current monthly fee</h2>
        <p className="pay-amount">{current ? kwd(current.monthly_amount) : '—'}</p>
        {current && <p className="hint">{startLabel(current.effective_from)}</p>}
      </section>

      <form className="card highlight-card" onSubmit={addRate}>
        <h2>Change the monthly fee</h2>
        <p className="hint">
          Choose the new fee and the month it starts. It can start this month or later, never in
          the past.
        </p>

        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}

        <div className="form-row">
          <label>
            New monthly fee (KWD)
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
            Starting from
            <input
              type="month"
              value={month}
              min={currentMonth()}
              onChange={(event) => event.target.value && setMonth(event.target.value)}
              required
            />
          </label>
        </div>

        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Set new fee'}
        </button>
      </form>

      <section className="card">
        <h2>Rate history</h2>

        <table>
          <thead>
            <tr>
              <th>Starts</th>
              <th>Monthly fee</th>
              <th>Set by</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {rates.map((rate) => {
              const upcoming = rate.effective_from > thisMonth

              return (
                <tr key={rate.fee_rate_id}>
                  <td>
                    {startLabel(rate.effective_from)}
                    {upcoming && <span className="badge muted-badge">Upcoming</span>}
                  </td>
                  <td className="money">{kwd(rate.monthly_amount)}</td>
                  <td>{rate.changed_by_name ?? <span className="muted">Set up with the app</span>}</td>
                  <td className="row-actions">
                    {upcoming && (
                      <button className="secondary danger-text small" onClick={() => removeRate(rate)}>
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>
    </>
  )
}