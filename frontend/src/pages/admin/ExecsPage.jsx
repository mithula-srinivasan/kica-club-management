import { useEffect, useState } from 'react'
import { api } from '../../api'
import { useAuth } from '../../auth'

export default function ExecsPage() {
  const { user } = useAuth()
  const [execs, setExecs] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    api('/execs/')
      .then(setExecs)
      .catch((err) => setError(err.message))
  }, [])

  async function changeExec(exec, action, question, doneMessage) {
    if (!window.confirm(question)) {
      return
    }

    setError('')
    setMessage('')

    try {
      await api(`/execs/${exec.exec_id}/${action}`, { method: 'POST' })

      // Stepping down as admin: reload the app so your own menus update
      if (exec.exec_id === user.exec_id && action === 'remove-admin') {
        window.location.assign('/')
        return
      }

      setExecs(await api('/execs/'))
      setMessage(doneMessage)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <h2>Execs</h2>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      {execs === null ? (
        <p className="hint">Loading...</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {execs.map((exec) => {
                const isMe = exec.exec_id === user.exec_id

                return (
                  <tr key={exec.exec_id}>
                    <td>
                      {exec.name}
                      {isMe && <span className="muted"> (you)</span>}
                    </td>
                    <td>{exec.email}</td>
                    <td>{exec.role === 'admin' ? <span className="badge">Admin</span> : 'Exec'}</td>
                    <td>{exec.is_active ? 'Active' : <span className="muted">Inactive</span>}</td>
                    <td className="row-actions">
                      <div className="row-buttons">
                          {exec.role === 'admin' ? (
                          !isMe && (
                            <button
                              className="secondary small"
                              onClick={() =>
                                changeExec(
                                  exec,
                                  'remove-admin',
                                  `Remove admin access from ${exec.name}?`,
                                  `${exec.name} is no longer an admin.`
                                )
                              }
                            >
                              Remove admin
                            </button>
                          )
                        ) : (
                          exec.is_active && (
                            <button
                              className="secondary small"
                              onClick={() =>
                                changeExec(
                                  exec,
                                  'make-admin',
                                  `Make ${exec.name} an admin? They will be able to approve sign-ups, manage Execs and correct anyone's records.`,
                                  `${exec.name} is now an admin.`
                                )
                              }
                            >
                              Make admin
                            </button>
                          )
                        )}

                        {!isMe &&
                          (exec.is_active ? (
                            <button
                              className="secondary danger-text small"
                              onClick={() =>
                                changeExec(
                                  exec,
                                  'deactivate',
                                  `Deactivate ${exec.name}? They will be logged out everywhere and won't be able to log in. Their records are kept.`,
                                  `${exec.name} has been deactivated.`
                                )
                              }
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              className="secondary small"
                              onClick={() =>
                                changeExec(
                                  exec,
                                  'reactivate',
                                  `Reactivate ${exec.name}? They will be able to log in again.`,
                                  `${exec.name} has been reactivated.`
                                )
                              }
                            >
                              Reactivate
                            </button>
                          ))}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}