import { useEffect, useState } from 'react'
import { api } from '../../api'

export default function SignupsPage() {
  const [pending, setPending] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    api('/execs/pending')
      .then(setPending)
      .catch((err) => setError(err.message))
  }, [])

  function removeFromList(exec) {
    setPending((current) => current.filter((e) => e.exec_id !== exec.exec_id))
  }

  async function approve(exec) {
    setError('')
    setMessage('')

    try {
      await api(`/execs/${exec.exec_id}/approve`, { method: 'POST' })
      removeFromList(exec)
      setMessage(`${exec.name} has been approved and can now log in.`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function reject(exec) {
    if (!window.confirm(`Reject the sign-up from ${exec.name} (${exec.email})? Their request will be deleted.`)) {
      return
    }

    setError('')
    setMessage('')

    try {
      await api(`/execs/${exec.exec_id}`, { method: 'DELETE' })
      removeFromList(exec)
      setMessage(`The sign-up from ${exec.name} was rejected.`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <h2>Waiting for approval</h2>
      <p className="hint">Only approve people you know are on the KICA committee.</p>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      {pending === null ? (
        <p className="hint">Loading...</p>
      ) : pending.length === 0 ? (
        <p className="hint">No sign-ups are waiting.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {pending.map((exec) => (
                <tr key={exec.exec_id}>
                  <td>{exec.name}</td>
                  <td>{exec.email}</td>
                  <td className="row-actions">
                    <div className="row-buttons">
                      <button className="small" onClick={() => approve(exec)}>
                        Approve
                      </button>
                      <button className="secondary danger-text small" onClick={() => reject(exec)}>
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}