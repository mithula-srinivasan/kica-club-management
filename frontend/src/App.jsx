import { Navigate, BrowserRouter, Route, Routes } from 'react-router-dom'
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
import ExpensesPage from './pages/ExpensesPage'
import TransfersPage from './pages/TransfersPage'
import AdminLayout from './pages/admin/AdminLayout'
import ExecsPage from './pages/admin/ExecsPage'
import SignupsPage from './pages/admin/SignupsPage'
import FeeAdjustmentsPage from './pages/admin/FeeAdjustmentsPage'
import OpeningBalancesPage from './pages/admin/OpeningBalancesPage'
import ActivityLogPage from './pages/admin/ActivityLogPage'



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
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/transfers" element={<TransfersPage />} />
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<Navigate to="signups" replace />} />
              <Route path="signups" element={<SignupsPage />} />
              <Route path="execs" element={<ExecsPage />} />
              <Route path="fees" element={<FeeAdjustmentsPage />} />
              <Route path="opening-balances" element={<OpeningBalancesPage />} />
              <Route path="activity" element={<ActivityLogPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}