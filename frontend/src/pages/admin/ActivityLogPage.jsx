import { useEffect, useState } from 'react'
import { api } from '../../api'
import { formatTimestamp } from '../../format'

const ACTIONS = {
  CREATE: 'Added',
  UPDATE: 'Changed',
  DELETE: 'Removed',
  REVERSE: 'Reversed',
  FINALIZE: 'Finalised',
}

const TABLES = {
  players: 'Player',
  club_sessions: 'Session',
  payments: 'Payment',
  fee_adjustments: 'Fee adjustment',
  expenses: 'Expense',
  transfers: 'Transfer',
  execs: 'Exec account',
  exec_opening_balances: 'Exec opening cash',
  player_opening_balances: 'Member opening balance',
  incomes: 'Income',
  fee_rates: 'Fee rate',
}

// "collected_by_exec_id" -> "Collected by exec", "kica_id" -> "Kica"
function fieldLabel(key) {
  const words = key.replace(/_ids?$/, '').replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export default function ActivityLogPage() {
  const [entries, setEntries] = useState(null)
  const [players, setPlayers] = useState([])
  const [execs, setExecs] = useState([])
  const [tableName, setTableName] = useState('')
  const [execId, setExecId] = useState('')
  const [error, setError] = useState('')

  // Names, so the log can show "Ahmed" instead of "#12"
  useEffect(() => {
    Promise.all([api('/players/'), api('/execs/')])
      .then(([playerData, execData]) => {
        setPlayers(playerData)
        setExecs(execData)
      })
      .catch((err) => setError(err.message))
  }, [])

  // Reload the log whenever a filter changes
  useEffect(() => {
    let ignore = false
    const params = { limit: 100 }

    if (tableName) params.table_name = tableName
    if (execId) params.exec_id = execId

    api('/audit-logs/', { params })
      .then((data) => {
        if (!ignore) {
          setEntries(data)
          setError('')
        }
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [tableName, execId])

  const playerNames = new Map(players.map((player) => [player.player_id, player.name]))
  const execNames = new Map(execs.map((exec) => [exec.exec_id, exec.name]))

  function playerName(id) {
    return playerNames.get(id) ?? `#${id}`
  }

  function execName(id) {
    return execNames.get(id) ?? `#${id}`
  }

  function showValue(key, value) {
    if (value === null || value === undefined) return '—'
    if (key === 'player_id') return playerName(value)
    if (key.endsWith('exec_id')) return execName(value)
    if (key === 'present_player_ids') {
      return value.length === 0 ? 'nobody' : value.map(playerName).join(', ')
    }
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    return String(value)
  }

  function describeRecord(entry) {
    const label = TABLES[entry.table_name] ?? entry.table_name

    if (entry.table_name === 'players' || entry.table_name === 'player_opening_balances') {
      return `${label}: ${playerName(entry.record_id)}`
    }

    if (entry.table_name === 'execs' || entry.table_name === 'exec_opening_balances') {
      return `${label}: ${execNames.get(entry.record_id) ?? entry.old_values?.name ?? `#${entry.record_id}`}`
    }

    return `${label} #${entry.record_id}`
  }

  function Details({ entry }) {
    const oldValues = entry.old_values ?? {}
    const newValues = entry.new_values ?? {}
    const keys = [...new Set([...Object.keys(oldValues), ...Object.keys(newValues)])]
    const isChange = entry.old_values && entry.new_values

    return (
      <ul className="change-list">
        {keys.map((key) => (
          <li key={key}>
            <span className="muted">{fieldLabel(key)}:</span>{' '}
            {isChange && key in oldValues
              ? `${showValue(key, oldValues[key])} → ${showValue(key, newValues[key])}`
              : showValue(key, newValues[key] ?? oldValues[key])}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <section className="card">
      <h2>Activity log</h2>
      <p className="hint">Every important change in the app, newest first. Showing the latest 100.</p>

      <div className="toolbar activity-filters">
        <label className="inline-label">
          What
          <select value={tableName} onChange={(event) => setTableName(event.target.value)}>
            <option value="">All activity</option>
            {Object.entries(TABLES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="inline-label">
          Who
          <select value={execId} onChange={(event) => setExecId(event.target.value)}>
            <option value="">All Execs</option>
            {execs.map((exec) => (
              <option key={exec.exec_id} value={exec.exec_id}>
                {exec.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      {entries === null ? (
        <p className="hint">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="hint">No activity found.</p>
      ) : (
        <div className="table-scroll">
          <table className="activity-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Who</th>
                <th>What</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.audit_id}>
                  <td className="nowrap">{formatTimestamp(entry.created_at)}</td>
                  <td>{entry.exec_name}</td>
                  <td>
                    <strong>{ACTIONS[entry.action] ?? entry.action}</strong>
                    <br />
                    <span className="muted">{describeRecord(entry)}</span>
                  </td>
                  <td>
                    <Details entry={entry} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}