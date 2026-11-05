import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <p className="loading">Loading...</p>
  }

  if (!user) {
    return <Navigate to="/exec/login" replace />
  }

  return children
}