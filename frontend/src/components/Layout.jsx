import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth'
import GlobalSearch from './GlobalSearch'

const LINKS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/fees', label: 'Fee Collection'},
  { to: '/attendance', label: 'Attendance' },
  { to: '/players', label: 'Players' },
  { to: '/expenses', label: 'Club Expenses' },
  { to: '/transfers', label: 'Money Transfers' },
]

function hideIfMissing(event) {
  event.currentTarget.style.display = 'none'
}

export default function Layout() {
  const { user, logOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const links = user.role === 'admin' ? [...LINKS, { to: '/admin', label: 'Admin' }] : LINKS

  return (
    <div className="shell">
      <aside className={menuOpen ? 'sidebar open' : 'sidebar'}>
        <div className="brand">
          <img src="/kica-logo.png" alt="" className="brand-logo" onError={hideIfMissing} />
          <span>KICA</span>
        </div>

        <nav className="side-nav" onClick={() => setMenuOpen(false)}>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
            >
              {link.label}
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
            aria-label="Open menu"
            aria-expanded={menuOpen}
          >
            ☰
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