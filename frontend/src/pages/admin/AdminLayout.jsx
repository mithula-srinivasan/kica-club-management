import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../auth'

export default function AdminLayout() {
  const { user } = useAuth()

  if (user.role !== 'admin') {
    return <p className="error">This area is for admins only.</p>
  }

  return (
    <div className="page">
      <h1>Admin</h1>

      <nav className="sub-tabs">
        <NavLink to="signups">Sign-ups</NavLink>
        <NavLink to="execs">Execs</NavLink>
        <NavLink to="fees">Fee adjustments</NavLink>
        <NavLink to="opening-balances">Opening balances</NavLink>
        <NavLink to="activity">Activity log</NavLink>
      </nav>

      <Outlet />
    </div>
  )
}