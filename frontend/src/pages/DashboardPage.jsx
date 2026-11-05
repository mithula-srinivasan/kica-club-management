import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import Figure from '../components/Figure'
import { currentMonth, kwd, monthLabel } from '../format'

export default function DashboardPage() {
  const [month, setMonth] = useState(currentMonth)
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    api('/dashboard/', { params: { month: `${month}-01` } })
      .then((data) => {
        if (!ignore) {
          setDashboard(data)
          setError('')
        }
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [month])

  if (error) {
    return <p className="error">{error}</p>
  }

  if (!dashboard) {
    return <p className="loading">Loading...</p>
  }

  const summary = dashboard.month

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <section className="stats">
        <Stat label="Club balance" value={kwd(dashboard.club_balance)} />
        <Stat
          label="Owed by members"
          value={kwd(dashboard.total_outstanding)}
          note={`${dashboard.players_owing} players owing · See who →`}
          to="/exec/fees"
        />
        <Stat label="Paid in advance" value={kwd(dashboard.total_credit)} />
        <Stat label="Active players" value={dashboard.active_players} />
      </section>

      <section className="card">
        <h2>Cash held by Execs</h2>

        {dashboard.cash_held.length === 0 ? (
          <p className="hint">No club money recorded yet.</p>
        ) : (
          <table>
            <tbody>
              {dashboard.cash_held.map((row) => (
                <tr key={row.exec_id}>
                  <td>{row.name}</td>
                  <td className="amount">{kwd(row.amount)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>Total</td>
                <td className="amount">{kwd(dashboard.club_balance)}</td>
              </tr>
            </tfoot>
          </table>
        )}
      </section>

      <section className="card">
        <div className="section-header">
          <h2>{monthLabel(summary.month)}</h2>
          <input
            type="month"
            value={month}
            onChange={(event) => event.target.value && setMonth(event.target.value)}
            aria-label="Choose month"
          />
        </div>

        <div className="figures">
          <Figure label="Sessions held" value={summary.sessions_held} />
          <Figure label="Players attended" value={summary.players_attended} />
          <Figure label="Total owed for the month" value={kwd(summary.fees_assessed)} />
          <Figure label="Fees received" value={kwd(summary.payments_received)} />
          <Figure label="Income received" value={kwd(summary.income_received)} />
          <Figure label="Expenses paid" value={kwd(summary.expenses_paid)} />
          <Figure label="Expenses paid" value={kwd(summary.expenses_paid)} />
        </div>

        <p className="section-link">
          <Link to="/exec/fees">See who hasn't paid →</Link>
        </p>
      </section>
    </div>
  )
}

function Stat({ label, value, note, to }) {
  const content = (
    <>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {note && <span className="hint">{note}</span>}
    </>
  )

  if (to) {
    return (
      <Link to={to} className="card stat stat-link">
        {content}
      </Link>
    )
  }

  return <div className="card stat">{content}</div>
}