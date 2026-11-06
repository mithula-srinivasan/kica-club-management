import { Link, Outlet } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

// Wraps the exec login, sign-up and password pages, adding a way back to the public website
export default function AuthLayout() {
  return (
    <div className="auth-layout">
      <Link to="/" className="back-to-site">
        <ArrowLeft size={18} aria-hidden="true" />
        Back to KICA website
      </Link>
      <Outlet />
    </div>
  )
}