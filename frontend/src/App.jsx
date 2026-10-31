import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import LoginPage from './pages/LoginPage'
import Placeholder from './pages/Placeholder'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Placeholder title="Dashboard" />} />
            <Route path="/players" element={<Placeholder title="Players" />} />
            <Route path="/attendance" element={<Placeholder title="Attendance" />} />
            <Route path="/payments" element={<Placeholder title="Payments" />} />
            <Route path="/expenses" element={<Placeholder title="Expenses" />} />
            <Route path="/transfers" element={<Placeholder title="Transfers" />} />
            <Route path="/admin" element={<Placeholder title="Admin" />} />
          </Route>

          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}