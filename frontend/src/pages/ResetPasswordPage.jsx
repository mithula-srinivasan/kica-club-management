import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { MIN_PASSWORD_LENGTH } from '../auth'

function tokenFromAddress() {
  // The email link looks like /reset-password#token=...
  // The part after # stays in the browser and is never sent to any server's logs
  return new URLSearchParams(window.location.hash.slice(1)).get('token')
}

export default function ResetPasswordPage() {
  const [token] = useState(tokenFromAddress)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }

    if (password !== confirmPassword) {
      setError('The two passwords do not match.')
      return
    }

    setSubmitting(true)

    try {
      await api('/auth/reset-password', {
        method: 'POST',
        body: { token, new_password: password },
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (!token) {
    return (
      <div className="auth-page">
        <div className="card">
          <h1>Link incomplete</h1>
          <p>This reset link is missing its code. Please request a new one.</p>
          <Link to="/exec/forgot-password">Request a new link</Link>
        </div>
      </div>
    )
  }

  if (done) {
    return (
      <div className="auth-page">
        <div className="card">
          <h1>Password changed</h1>
          <p>
            Your new password is set. For safety, you've been logged out on all
            your devices.
          </p>
          <Link to="/exec/login">Log in</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <form className="card" onSubmit={handleSubmit}>
        <h1>Choose a new password</h1>

        {error && <p className="error">{error}</p>}

        <label>
          New password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
          <span className="hint">At least {MIN_PASSWORD_LENGTH} characters.</span>
        </label>

        <label>
          Confirm new password
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : 'Set new password'}
        </button>
      </form>
    </div>
  )
}