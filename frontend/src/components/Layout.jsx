import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import GlobalSearch from './GlobalSearch'

const LINKS = [
  { to: '/exec', label: 'Dashboard', end: true },
  { to: '/exec/attendance', label: 'Attendance' },
  { to: '/exec/players', label: 'Players' },
  { to: '/exec/registrations', label: 'Registrations', showsPendingCount: true },
  { to: '/exec/fees', label: 'Fee Collection' },
  { to: '/exec/expenses', label: 'Expenses' },
  { to: '/exec/income', label: 'Income' },
  { to: '/exec/transfers', label: 'Money Transfers' },
]

function hideIfMissing(event) {
  event.currentTarget.style.display = 'none'
}

// How many player registrations are waiting. Checked when you move between pages,
// every minute, and straight away when the Registrations page says something changed.
function usePendingRegistrations() {
  const location = useLocation()
  const [count, setCount] = useState(0)

  useEffect(() => {
    let ignore = false

    function load() {
      api('/registrations/pending-count')
        .then((data) => {
          if (!ignore) setCount(data.count)
        })
        .catch(() => {})
    }

    load()
    const timer = setInterval(load, 60 * 1000)
    window.addEventListener('registrations-changed', load)

    // Clean up when leaving, so we don't keep checking twice
    return () => {
      ignore = true
      clearInterval(timer)
      window.removeEventListener('registrations-changed', load)
    }
  }, [location.pathname])

  return count
}

export default function Layout() {
  const { user, logOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const pendingCount = usePendingRegistrations()

  const links = user.role === 'admin' ? [...LINKS, { to: '/exec/admin', label: 'Admin' }] : LINKS

  return (
    <div className="shell">
      <aside className={menuOpen ? 'sidebar open' : 'sidebar'}>
        <div className="brand">
          <img src="/kica-logo.png" alt="" className="brand-logo" onError={hideIfMissing} />
          <span>KICA</span>
        </div>

        <nav className="side-nav" onClick={() => setMenuOpen(false)}>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end}>
              {link.label}
              {link.showsPendingCount && pendingCount > 0 && (
                <span className="nav-count" aria-label={`${pendingCount} waiting`}>
                  {pendingCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <span className="sidebar-name">{user.name}</span>
          {user.role === 'admin' && <span className="badge">Admin</span>}
          <button className="secondary small" onClick={logOut}>
            Log out
          </button>
        </div>
      </aside>

      {menuOpen && <div className="backdrop" onClick={() => setMenuOpen(false)} />}

      <div className="content">
        <header className="top-bar">
          <button
            className="secondary menu-button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label={pendingCount > 0 ? `Open menu (${pendingCount} registrations waiting)` : 'Open menu'}
            aria-expanded={menuOpen}
          >
            ☰
            {pendingCount > 0 && <span className="nav-count">{pendingCount}</span>}
          </button>
          <span className="top-brand">KICA</span>
          <GlobalSearch />
        </header>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  )
}