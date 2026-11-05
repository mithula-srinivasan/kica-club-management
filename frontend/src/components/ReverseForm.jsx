import { useState } from 'react'

export default function ReverseForm({
  label,
  confirmMessage,
  buttonText,
  onReverse,
  onCancel,
  placeholder = 'e.g. entered the wrong amount',
  savingText = 'Reversing...',
}) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (!reason.trim()) {
      setError('Please give a reason.')
      return
    }

    if (!window.confirm(confirmMessage)) {
      return
    }

    setSaving(true)

    try {
      await onReverse(reason.trim())
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <form className="reverse-form" onSubmit={handleSubmit}>
      <label>
        {label}
        <input
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          maxLength={500}
          placeholder={placeholder}
          autoFocus
        />
      </label>

      {error && <p className="error">{error}</p>}

      <div className="actions">
        <button type="submit" className="danger" disabled={saving}>
          {saving ? savingText : buttonText}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}