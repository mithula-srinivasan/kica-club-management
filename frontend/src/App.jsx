import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import LoginPage from './pages/LoginPage'
import Placeholder from './pages/Placeholder'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import PlayersPage from './pages/PlayersPage'
import PlayerPage from './pages/PlayerPage'
import AttendancePage from './pages/AttendancePage'
import SessionPage from './pages/SessionPage'
import FeeCollectionPage from './pages/FeeCollectionPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/players/:playerId" element={<PlayerPage />} />
            <Route path="/attendance" element={<AttendancePage />} />
            <Route path="/attendance/:sessionId" element={<SessionPage />} />
            <Route path="/fees" element={<FeeCollectionPage />} />
            <Route path="/expenses" element={<Placeholder title="Club Expenses" />} />
            <Route path="/transfers" element={<Placeholder title="Money Transfers" />} />
            <Route path="/admin" element={<Placeholder title="Admin" />} />
          </Route>

          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}