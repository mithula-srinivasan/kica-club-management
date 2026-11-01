import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

// Every page or feature an Exec might search for, with words people are likely to type
const FEATURES = [
  { label: 'Dashboard', to: '/', keywords: 'home overview club balance cash held summary month' },
  { label: 'Record a payment', to: '/fees', keywords: 'fee collection pay payment collect money record' },
  { label: 'Who owes', to: '/fees', keywords: 'owes owing outstanding unpaid pending debt fees' },
  { label: 'Recent payments', to: '/fees', keywords: 'payments history reverse mistake' },
  { label: 'Attendance', to: '/attendance', keywords: 'attendance session sessions mark present create' },
  { label: 'Players', to: '/players', keywords: 'players members list add new player' },
  { label: 'Club Expenses', to: '/expenses', keywords: 'expenses expense spend spent hall rental costs' },
  { label: 'Money Transfers', to: '/transfers', keywords: 'transfers transfer handover cash received money' },
  { label: 'Approve sign-ups', to: '/admin/signups', keywords: 'admin approve sign-ups signups pending reject', admin: true },
  { label: 'Manage Execs', to: '/admin/execs', keywords: 'admin execs exec deactivate reactivate make admin', admin: true },
  { label: 'Fee adjustments', to: '/admin/fees', keywords: 'admin waive waiver discount adjust adjustment fee', admin: true },
  { label: 'Fee rate', to: '/admin/fee-rate', keywords: 'admin fee rate monthly fee price change amount 5 kwd', admin: true },
  { label: 'Opening balances', to: '/admin/opening-balances', keywords: 'admin opening balances starting figures excel', admin: true },
  { label: 'Activity log', to: '/admin/activity', keywords: 'admin activity audit log history changes', admin: true },
  { label: 'Download club data', to: '/admin/backup', keywords: 'admin backup download export excel data', admin: true },
]

export default function GlobalSearch() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [players, setPlayers] = useState([])
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)

  // Load players when the box is clicked, so newly added players are always included
  function loadPlayers() {
    api('/players/')
      .then(setPlayers)
      .catch(() => {})
  }

  const term = search.trim().toLowerCase()

  const featureResults = term
    ? FEATURES.filter((feature) => !feature.admin || user.role === 'admin')
        .filter((feature) => `${feature.label} ${feature.keywords}`.toLowerCase().includes(term))
        .slice(0, 4)
        .map((feature) => ({ key: `page-${feature.label}`, label: feature.label, to: feature.to }))
    : []

  const playerResults = term
    ? players
        .filter(
          (player) =>
            player.name.toLowerCase().includes(term) ||
            (player.kica_id ?? '').toLowerCase().includes(term)
        )
        .slice(0, 6)
        .map((player) => ({
          key: `player-${player.player_id}`,
          label: player.name,
          detail: `${player.kica_id ?? ''}${player.is_active ? '' : ' · inactive'}`,
          to: `/players/${player.player_id}`,
        }))
    : []

  const allResults = [...featureResults, ...playerResults]

  function choose(result) {
    setSearch('')
    setOpen(false)
    navigate(result.to)
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && allResults.length > 0) {
      event.preventDefault()
      choose(allResults[0])
    }

    if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  function ResultGroup({ title, results }) {
    if (results.length === 0) {
      return null
    }

    return (
      <>
        <li className="search-group">{title}</li>
        {results.map((result) => (
          <li key={result.key}>
            <button
              type="button"
              className="picker-option"
              // Stops the box losing focus before the click registers
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(result)}
            >
              <span>{result.label}</span>
              {result.detail && <span className="muted">{result.detail}</span>}
            </button>
          </li>
        ))}
      </>
    )
  }

  return (
    <div className="global-search">
      <input
        type="search"
        placeholder="Search"
        value={search}
        onFocus={() => {
          loadPlayers()
          setOpen(true)
        }}
        onChange={(event) => {
          setSearch(event.target.value)
          setOpen(true)
        }}
        onKeyDown={handleKeyDown}
        onBlur={() => setOpen(false)}
        aria-label="Search pages and players"
      />

      {open && term && (
        <ul className="picker-list search-results">
          {allResults.length === 0 ? (
            <li className="search-empty">No results</li>
          ) : (
            <>
              <ResultGroup title="Pages" results={featureResults} />
              <ResultGroup title="Players" results={playerResults} />
            </>
          )}
        </ul>
      )}
    </div>
  )
}