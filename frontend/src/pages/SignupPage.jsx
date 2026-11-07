import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { MIN_PASSWORD_LENGTH } from '../auth'

export default function SignupPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
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
      await api('/auth/signup', {
        method: 'POST',
        body: { name, email, password },
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className="auth-page">
        <div className="card">
          <h1>Sign-up received</h1>
          <p>
            An admin needs to approve your account before you can log in.
            You'll be able to log in once they have.
          </p>
          <Link to="/exec/login">Back to login</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <form className="card" onSubmit={handleSubmit}>
        <img
          src="/kica-logo.png"
          alt="KICA"
          className="auth-logo"
          onError={(event) => {
            event.currentTarget.style.display = 'none'
          }}
        />
        <h1>Create an account</h1>
        <p className="warning">
          For the KICA executive team only. Not for players or parents.
        </p>
        {error && <p className="error">{error}</p>}

        <label>
          Full name
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            autoComplete="name"
            required
          />
        </label>

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

        <label>
          Password
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
          Confirm password
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </label>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating account...' : 'Create account'}
        </button>

        <div className="auth-links">
          <Link to="/exec/login">Already have an account? Log in</Link>
        </div>
      </form>
    </div>
  )
}