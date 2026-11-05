import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { genderLabel } from '../components/PlayerDetailsFields'
import ReverseForm from '../components/ReverseForm'
import { formatDate, formatTimestamp, whatsAppLink } from '../format'


// [value for the backend, tab name]
const VIEWS = [
  ['pending', 'Waiting'],
  ['approved', 'Approved'],
  ['rejected', 'Rejected'],
]

const EMPTY_MESSAGES = {
  pending: 'No registrations are waiting.',
  approved: 'No registrations have been approved yet.',
  rejected: 'No registrations have been rejected.',
}

// Tell the menu to update its count badge straight away
function registrationsChanged() {
  window.dispatchEvent(new Event('registrations-changed'))
}

// Age in whole years today, e.g. "2014-05-20" -> 12
function ageToday(dateOfBirth) {
  const born = new Date(`${dateOfBirth}T00:00:00`)
  const now = new Date()
  const years = now.getFullYear() - born.getFullYear()

  const hadBirthdayThisYear =
    now.getMonth() > born.getMonth() ||
    (now.getMonth() === born.getMonth() && now.getDate() >= born.getDate())

  return hadBirthdayThisYear ? years : years - 1
}

export default function RegistrationsPage() {
  const [show, setShow] = useState('pending')
  const [registrations, setRegistrations] = useState(null)
  const [rejectingId, setRejectingId] = useState(null)
  const [error, setError] = useState('')
  // { text, playerId } after approving or rejecting
  const [message, setMessage] = useState(null)

  // Load the list for the chosen tab
  useEffect(() => {
    let ignore = false

    api('/registrations/', { params: { show } })
      .then((data) => {
        if (!ignore) setRegistrations(data)
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })

    return () => {
      ignore = true
    }
  }, [show])

  function changeView(view) {
    setShow(view)
    setRegistrations(null)
    setRejectingId(null)
    setMessage(null)
    setError('')
  }

  function removeFromList(registration) {
    setRegistrations((current) =>
      current.filter((r) => r.registration_id !== registration.registration_id)
    )
  }

  async function approve(registration) {
    const question =
      `Add ${registration.name} as a new player?\n\n` +
      'They will get the next KICA ID, with today as their joined date.'

    if (!window.confirm(question)) {
      return
    }

    setError('')
    setMessage(null)

    try {
      const player = await api(`/registrations/${registration.registration_id}/approve`, {
        method: 'POST',
      })

      removeFromList(registration)
      setMessage({ text: `${player.name} was added as ${player.kica_id}.`, playerId: player.player_id })
      registrationsChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  async function reject(registration, reason) {
    await api(`/registrations/${registration.registration_id}/reject`, {
      method: 'POST',
      body: { reason },
    })

    removeFromList(registration)
    setRejectingId(null)
    setMessage({ text: `The registration for ${registration.name} was rejected.` })
    registrationsChanged()
  }

  return (
    <div className="page">
      <h1>Player registrations</h1>
      <p className="hint">Sign-ups from the public “Join KICA” form.</p>

      <div className="tabs">
        {VIEWS.map(([view, label]) => (
          <button
            key={view}
            className={show === view ? 'small' : 'secondary small'}
            aria-pressed={show === view}
            onClick={() => changeView(view)}
          >
            {label}
          </button>
        ))}
      </div>

      {error && <p className="error">{error}</p>}

      {message && (
        <p className="success">
          {message.text}
          {message.playerId && (
            <>
              {' '}
              <Link to={`/exec/players/${message.playerId}`}>Open player</Link>
            </>
          )}
        </p>
      )}

      {registrations === null ? (
        <p className="loading">Loading...</p>
      ) : registrations.length === 0 ? (
        <p className="hint">{EMPTY_MESSAGES[show]}</p>
      ) : show === 'pending' ? (
        <div className="registration-list">
          {registrations.map((registration) => (
            <PendingRegistration
              key={registration.registration_id}
              registration={registration}
              rejecting={rejectingId === registration.registration_id}
              onApprove={() => approve(registration)}
              onStartReject={() => setRejectingId(registration.registration_id)}
              onCancelReject={() => setRejectingId(null)}
              onReject={(reason) => reject(registration, reason)}
            />
          ))}
        </div>
      ) : (
        <ReviewedTable registrations={registrations} show={show} />
      )}
    </div>
  )
}

/* ---------- One registration waiting for a decision ---------- */

function PendingRegistration({
  registration: r,
  rejecting,
  onApprove,
  onStartReject,
  onCancelReject,
  onReject,
}) {
  const notSet = <span className="muted">—</span>

  return (
    <section className="card registration-card">
      <div className="section-header">
        <h2>{r.name}</h2>
        <span className="hint">Sent {formatTimestamp(r.submitted_at)}</span>
      </div>

      <dl className="details">
        <div>
          <dt>Date of birth</dt>
          <dd>
            {formatDate(r.date_of_birth)} (age {ageToday(r.date_of_birth)})
          </dd>
        </div>

                <div>
          <dt>Country</dt>
          <dd>{r.country}</dd>
        </div>

        <div>
          <dt>Gender</dt>
          <dd>{genderLabel(r.gender) ?? notSet}</dd>
        </div>
        <div>
          <dt>FIDE ID</dt>
          <dd>{r.fide_id ?? notSet}</dd>
        </div>
        <div>
          <dt>Parent</dt>
          <dd>{r.parent_name}</dd>
        </div>
        <div>
          <dt>WhatsApp number</dt>
          <dd>
            <a href={whatsAppLink(r.phone_1)} target="_blank" rel="noopener noreferrer">
              {r.phone_1}
            </a>
          </dd>
        </div>
        <div>
          <dt>Second phone</dt>
          <dd>
            {r.phone_2 ? (
              <a href={`tel:${r.phone_2.replace(/\s/g, '')}`}>{r.phone_2}</a>
            ) : (
              notSet
            )}
          </dd>
        </div>
        <div className="full-row">
          <dt>Email</dt>
          <dd>
            <a href={`mailto:${r.email}`}>{r.email}</a>
          </dd>
        </div>
      </dl>

      <p className="hint">Agreed to the club rules on {formatTimestamp(r.consented_at)}.</p>

      {rejecting ? (
        <ReverseForm
          label="Reason for rejecting (only Execs see this)"
          placeholder="e.g. already a member"
          confirmMessage={`Reject the registration for ${r.name}?\n\nNo email is sent to the parent.`}
          buttonText="Reject registration"
          savingText="Rejecting..."
          onCancel={onCancelReject}
          onReverse={onReject}
        />
      ) : (
        <div className="actions">
          <button className="green" onClick={onApprove}>
            Approve and add player
          </button>
          <button className="secondary danger-text" onClick={onStartReject}>
            Reject
          </button>
        </div>
      )}
    </section>
  )
}

/* ---------- Approved or rejected registrations ---------- */

function ReviewedTable({ registrations, show }) {
  const approved = show === 'approved'

  return (
    <section className="card">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>{approved ? 'KICA ID' : 'Reason'}</th>
              <th>{approved ? 'Approved by' : 'Rejected by'}</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {registrations.map((r) => (
              <tr key={r.registration_id}>
                <td>
                  {approved && r.player_id ? (
                    <Link to={`/exec/players/${r.player_id}`}>{r.name}</Link>
                  ) : (
                    r.name
                  )}
                </td>
                <td>{approved ? r.kica_id : r.rejection_reason}</td>
                <td>{r.reviewed_by_name}</td>
                <td>{formatTimestamp(r.reviewed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}