import { useState } from 'react'

export default function PlayerPicker({ players, value, onChange }) {
  const [search, setSearch] = useState('')
  const selected = players.find((player) => player.player_id === value)

  if (selected) {
    return (
      <div className="picked">
        <span>
          <strong>{selected.name}</strong>{' '}
          <span className="muted">
            {selected.kica_id}
            {!selected.is_active && ' · inactive'}
          </span>
        </span>
        <button
          type="button"
          className="secondary small"
          onClick={() => {
            onChange(null)
            setSearch('')
          }}
        >
          Change
        </button>
      </div>
    )
  }

  const term = search.trim().toLowerCase()
  const matches = term
    ? players
        .filter(
          (player) =>
            player.name.toLowerCase().includes(term) ||
            (player.kica_id ?? '').toLowerCase().includes(term)
        )
        .slice(0, 8)
    : []

  return (
    <div className="picker">
      <input
        type="search"
        placeholder="Type a name or KICA ID"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        aria-label="Search for a player"
      />

      {term &&
        (matches.length === 0 ? (
          <p className="hint">No matching players.</p>
        ) : (
          <ul className="picker-list">
            {matches.map((player) => (
              <li key={player.player_id}>
                <button
                  type="button"
                  className="picker-option"
                  onClick={() => {
                    setSearch('')
                    onChange(player.player_id)
                  }}
                >
                  <span>{player.name}</span>
                  <span className="muted">
                    {player.kica_id}
                    {!player.is_active && ' · inactive'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ))}
    </div>
  )
}