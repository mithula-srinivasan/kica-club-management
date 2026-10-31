import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout() {
  const { user, logOut } = useAuth()

  return (
    <div className="app">
      <header className="top-bar">
        <span className="brand">KICA</span>

        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/players">Players</NavLink>
          <NavLink to="/attendance">Attendance</NavLink>
          <NavLink to="/payments">Payments</NavLink>
          <NavLink to="/expenses">Expenses</NavLink>
          <NavLink to="/transfers">Transfers</NavLink>
          {user.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
        </nav>

        <div className="user">
          <span>{user.name}</span>
          {user.role === 'admin' && <span className="badge">Admin</span>}
          <button className="secondary" onClick={logOut}>Log out</button>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  )
}