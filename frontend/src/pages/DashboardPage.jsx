import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { currentMonth, kwd, monthLabel } from '../format'
import Figure from '../components/Figure'

export default function DashboardPage() {
  const [month, setMonth] = useState(currentMonth)
  const [dashboard, setDashboard] = useState(null)
  const [owing, setOwing] = useState([])
  const [unpaid, setUnpaid] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    const params = { month: `${month}-01` }

    Promise.all([
      api('/dashboard/', { params }),
      api('/dashboard/outstanding'),
      api('/dashboard/unpaid', { params }),
    ])
      .then(([dashboardData, owingData, unpaidData]) => {
        if (ignore) return
        setDashboard(dashboardData)
        setOwing(owingData)
        setUnpaid(unpaidData)
        setError('')
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    // If the month changes before these replies arrive, ignore the old replies
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
  const label = monthLabel(summary.month)

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <section className="stats">
        <Stat label="Club balance" value={kwd(dashboard.club_balance)} />
        <Stat
          label="Owed by members"
          value={kwd(dashboard.total_outstanding)}
          note={`${dashboard.players_owing} players owing`}
        />
        <Stat label="Paid in advance" value={kwd(dashboard.total_credit)} />
        <Stat label="Active players" value={dashboard.active_players} />
      </section>

      <div className="two-columns">
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
          <h2>Who owes</h2>

          {owing.length === 0 ? (
            <p className="hint">Nobody owes anything.</p>
          ) : (
            <table>
              <tbody>
                {owing.map((row) => (
                  <tr key={row.player_id}>
                    <td>
                      <Link to={`/players/${row.player_id}`}>{row.player_name}</Link>
                    </td>
                    <td className="amount">{kwd(row.outstanding)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>

      <section className="card">
        <div className="section-header">
          <h2>{label}</h2>
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
          <Figure label="Fees for the month" value={kwd(summary.fees_assessed)} />
          <Figure label="Money received" value={kwd(summary.payments_received)} />
          <Figure label="Expenses paid" value={kwd(summary.expenses_paid)} />
        </div>

        <h3>Not yet paid for {label}</h3>

        {unpaid.length === 0 ? (
          <p className="hint">Everyone who attended has paid for this month.</p>
        ) : (
          <table>
            <tbody>
              {unpaid.map((row) => (
                <tr key={row.player_id}>
                  <td>
                    <Link to={`/players/${row.player_id}`}>{row.player_name}</Link>
                  </td>
                  <td className="amount">{kwd(row.outstanding)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value, note }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {note && <span className="hint">{note}</span>}
    </div>
  )
}
