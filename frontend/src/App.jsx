import { Navigate, BrowserRouter, Route, Routes, Link } from 'react-router-dom'
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
import BackupPage from './pages/admin/BackupPage'
import FeeRatePage from './pages/admin/FeeRatePage'
import IncomePage from './pages/IncomePage'
import JoinRegisterPage from './pages/JoinRegisterPage'
import RegistrationsPage from './pages/RegistrationsPage'
import PublicLayout from './public-site/PublicLayout'
import PublicPlaceholder from './public-site/PublicPlaceholder'
import HomePage from './public-site/HomePage'
import AuthLayout from './components/AuthLayout'
import AboutPage from './public-site/AboutPage'
import ActivitiesPage from './public-site/ActivitiesPage'



export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
            <Route element={<PublicLayout />}>
            <Route
              path="/"
              element={<HomePage />}
            />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/activities" element={<ActivitiesPage />} />
            <Route
              path="/membership"
              element={
                <PublicPlaceholder
                  title="Membership"
                  text="Join the Kuwait Indian Chess Association. Membership is 5 KWD per month."
                >
                  <Link to="/join/register" className="site-button">
                    Register a new player
                  </Link>
                </PublicPlaceholder>
              }
            />
            <Route path="/join/register" element={<JoinRegisterPage />} />
          </Route>

          {/* The link shared with parents */}
          <Route path="/join" element={<Navigate to="/membership" replace />} />
            <Route element={<AuthLayout />}>
            <Route path="/exec/login" element={<LoginPage />} />
            <Route path="/exec/signup" element={<SignupPage />} />
            <Route path="/exec/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/exec/reset-password" element={<ResetPasswordPage />} />
          </Route>
          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/exec" element={<DashboardPage />} />
            <Route path="/exec/players" element={<PlayersPage />} />
            <Route path="/exec/players/:playerId" element={<PlayerPage />} />
            <Route path="/exec/registrations" element={<RegistrationsPage />} />
            <Route path="/exec/attendance" element={<AttendancePage />} />
            <Route path="/exec/attendance/:sessionId" element={<SessionPage />} />
            <Route path="/exec/fees" element={<FeeCollectionPage />} />
            <Route path="/exec/expenses" element={<ExpensesPage />} />
            <Route path="/exec/income" element={<IncomePage />} />
            <Route path="/exec/transfers" element={<TransfersPage />} />
            <Route path="/exec/admin" element={<AdminLayout />}>
              <Route index element={<Navigate to="signups" replace />} />
              <Route path="signups" element={<SignupsPage />} />
              <Route path="execs" element={<ExecsPage />} />
              <Route path="fees" element={<FeeAdjustmentsPage />} />
              <Route path="fee-rate" element={<FeeRatePage />} />
              <Route path="opening-balances" element={<OpeningBalancesPage />} />
              <Route path="activity" element={<ActivityLogPage />} />
              <Route path="backup" element={<BackupPage />} />
            </Route>
          </Route>

          {/* The old login address, in case anyone saved it */}
          <Route path="/login" element={<Navigate to="/exec/login" replace />} />

          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}