import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'

// Admins only: every approved Exec, for the "on behalf of" dropdowns
export function useExecList() {
  const { user } = useAuth()
  const [execs, setExecs] = useState([])

  useEffect(() => {
    if (user.role !== 'admin') {
      return
    }

    api('/execs/')
      .then(setExecs)
      .catch(() => {})
  }, [user.role])

  return execs
}

// Shown to admins only. Regular Execs never see it, and are always the handler themselves.
export default function HandledBySelect({ label, execs, value, onChange, exclude }) {
  const { user } = useAuth()

  if (user.role !== 'admin') {
    return null
  }

  const others = execs.filter(
    (exec) => exec.exec_id !== user.exec_id && exec.exec_id !== exclude
  )

  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Me ({user.name})</option>
        {others.map((exec) => (
          <option key={exec.exec_id} value={exec.exec_id}>
            {`${exec.name}${exec.is_active ? '' : ' (inactive)'}`}
          </option>
        ))}
      </select>
    </label>
  )
}