import { Fragment, useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import ReverseForm from '../components/ReverseForm'
import { formatDate, kwd, today } from '../format'

export default function ExpensesPage() {
  const { user } = useAuth()
  const [expenses, setExpenses] = useState(null)
  const [reversingId, setReversingId] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/expenses/')
      .then(setExpenses)
      .catch((err) => setError(err.message))
  }, [])

  function reloadExpenses() {
    api('/expenses/')
      .then(setExpenses)
      .catch((err) => setError(err.message))
  }

  async function reverseExpense(expense, reason) {
    const updated = await api(`/expenses/${expense.expense_id}/reverse`, {
      method: 'POST',
      body: { reason },
    })
    setExpenses((current) =>
      current.map((e) => (e.expense_id === updated.expense_id ? updated : e))
    )
    setReversingId(null)
  }

  if (!expenses) {
    return error ? <p className="error">{error}</p> : <p className="loading">Loading...</p>
  }

  return (
    <div className="page">
      <h1>Club Expenses</h1>

      {error && <p className="error">{error}</p>}

      <RecordExpenseForm onRecorded={reloadExpenses} />

      <section className="card">
        <h2>Expense history</h2>

        {expenses.length === 0 ? (
          <p className="hint">No expenses recorded yet.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Paid by</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => {
                  const reversed = expense.status === 'reversed'
                  const canReverse =
                    !reversed &&
                    (user.role === 'admin' || expense.recorded_by_exec_id === user.exec_id)
                  const isReversing = reversingId === expense.expense_id

                  return (
                    <Fragment key={expense.expense_id}>
                      <tr className={reversed ? 'reversed' : undefined}>
                        <td>{formatDate(expense.expense_date)}</td>
                        <td>{expense.description}</td>
                        <td className="money">{kwd(expense.amount)}</td>
                        <td>
                          {expense.recorded_by_name}
                          {reversed && ' (reversed)'}
                        </td>
                        <td className="row-actions">
                          {canReverse && !isReversing && (
                            <button
                              className="secondary danger-text small"
                              onClick={() => setReversingId(expense.expense_id)}
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
                              label={`Reason for reversing "${expense.description}" (${kwd(expense.amount)})`}
                              confirmMessage={
                                `Reverse the expense "${expense.description}" of ${kwd(expense.amount)}?\n\n` +
                                'It will stay in the history, marked as reversed, and no longer count as money spent.'
                              }
                              buttonText="Reverse expense"
                              onCancel={() => setReversingId(null)}
                              onReverse={(reason) => reverseExpense(expense, reason)}
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

function RecordExpenseForm({ onRecorded }) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [expenseDate, setExpenseDate] = useState(today)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)

    try {
      const expense = await api('/expenses/', {
        method: 'POST',
        body: { description, amount, expense_date: expenseDate },
      })

      setMessage(`Recorded ${kwd(expense.amount)}: ${expense.description}.`)
      onRecorded()

      setDescription('')
      setAmount('')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card highlight-card" onSubmit={handleSubmit}>
      <h2>Record an expense</h2>
      <p className="hint">Money you paid from the club funds you are holding.</p>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <label>
        What was it for?
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          maxLength={500}
          placeholder="e.g. Hall rental – October"
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
          Date paid
          <input
            type="date"
            value={expenseDate}
            max={today()}
            onChange={(event) => setExpenseDate(event.target.value)}
            required
          />
        </label>
      </div>

      <button type="submit" className="button-large" disabled={saving}>
        {saving ? 'Saving...' : 'Record expense'}
      </button>
    </form>
  )
}