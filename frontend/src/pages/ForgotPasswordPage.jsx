import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await api('/auth/forgot-password', {
        method: 'POST',
        body: { email },
      })
      setSent(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (sent) {
    return (
      <div className="auth-page">
        <div className="card">
          <h1>Check your email</h1>
          <p>
            If an account exists for <strong>{email}</strong>, we've sent a link to
            reset your password. It works for 1 hour. Check your spam folder if you
            can't see it.
          </p>
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <form className="card" onSubmit={handleSubmit}>
        <h1>Forgot your password?</h1>
        <p className="hint">Enter your email and we'll send you a link to choose a new one.</p>

        {error && <p className="error">{error}</p>}

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Sending...' : 'Send reset link'}
        </button>

        <div className="auth-links">
          <Link to="/login">Back to login</Link>
        </div>
      </form>
    </div>
  )
}