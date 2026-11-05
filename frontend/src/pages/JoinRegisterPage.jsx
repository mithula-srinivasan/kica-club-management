import { useEffect, useRef, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { api } from '../api'
import {
  CountryOptions,
  PHONE_HINT,
  PHONE_PATTERN,
  useCountries,
} from '../components/PlayerDetailsFields'
import { today } from '../format'

const CLUB_EMAIL = 'kica.chesskwt@gmail.com'

// The "KICA Members" WhatsApp group. If the link is ever reset in WhatsApp,
// change it here: the button and the QR code both update.
const WHATSAPP_GROUP_LINK = 'https://chat.whatsapp.com/HsnonjfDkqE17FhdfmvqNv'

// [value sent to the backend, text shown next to the bullet]
const GENDERS = [
  ['male', 'Male'],
  ['female', 'Female'],
  ['other', 'Other'],
]

function emptyForm() {
  return {
    name: '',
    date_of_birth: '',
    gender: '',
    country: '',
    parent_name: '',
    email: '',
    phone_1: '+965 ',
    phone_2: '',
    fide_id: '',
    consent: false,
    // A hidden box people never see. Spam bots fill in every box they find.
    website: '',
  }
}

export default function JoinRegisterPage() {
  const countries = useCountries()
  const [values, setValues] = useState(emptyForm)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  // After a successful submit: { name, email } for the thank-you screen
  const [registered, setRegistered] = useState(null)
  const errorRef = useRef(null)

  // The browser tab's title
  useEffect(() => {
    document.title = 'Join KICA – Kuwait Indian Chess Association'
  }, [])

  // Bring the error message into view so it isn't missed (useful on phones)
  useEffect(() => {
    if (error) {
      errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [error])

  // Change one field, keep the others
  function setField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  // Gives a box its name, value and what to do when it changes
  function field(name) {
    return {
      name,
      value: values[name],
      onChange: (event) => setField(name, event.target.value),
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await api('/registrations/', { method: 'POST', body: values })

      setRegistered({ name: values.name.trim(), email: values.email.trim() })
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function registerAnother() {
    setValues(emptyForm())
    setRegistered(null)
    window.scrollTo({ top: 0 })
  }

  return (
    <div className="join-page">
      {/* Top: plain black, so the title is easy to read */}
      <div className="join-container">
        <header className="join-header">
          <img
            src="/kica-logo.png"
            alt="Kuwait Indian Chess Association logo"
            className="join-logo"
          />
          <div>
            <p className="join-eyebrow">Kuwait Indian Chess Association</p>
            <h1>Register a new player</h1>
            {!registered && (
              <p className="join-intro">
                Fill in the form below. Our team will review it and contact you soon.
              </p>
            )}
          </div>
        </header>
      </div>

      {/* From the cards down: the faint chessboard background */}
      <div className="join-board">
        <div className="join-container">
          {registered ? (
            <ThankYou
              name={registered.name}
              email={registered.email}
              onRegisterAnother={registerAnother}
            />
          ) : (
            <form className="join-form" onSubmit={handleSubmit}>
              {/* Top left */}
              <section className="join-card">
                <h2>Player details</h2>

                <Field label="Player's full name">
                  <input {...field('name')} maxLength={100} autoComplete="off" required />
                </Field>

                <Field label="Date of birth">
                  <input type="date" {...field('date_of_birth')} max={today()} required />
                </Field>

                <fieldset className="join-fieldset">
                  <legend className="join-label">Gender</legend>
                  <div className="join-radios">
                    {GENDERS.map(([value, text]) => (
                      <label key={value} className="join-radio">
                        <input
                          type="radio"
                          name="gender"
                          value={value}
                          checked={values.gender === value}
                          onChange={() => setField('gender', value)}
                          required
                        />
                        {text}
                      </label>
                    ))}
                  </div>
                </fieldset>

                <Field label="Country">
                  <select {...field('country')} required>
                    <CountryOptions countries={countries} />
                  </select>
                </Field>
              </section>

              {/* Top right */}
              <section className="join-card">
                <h2>Parent details</h2>

                <Field label="Parent's full name">
                  <input {...field('parent_name')} maxLength={100} autoComplete="name" required />
                </Field>

                <Field label="Email" hint="We'll send a confirmation here.">
                  <input
                    type="email"
                    {...field('email')}
                    maxLength={255}
                    autoComplete="email"
                    required
                  />
                </Field>

                <Field label="Whatsapp Number" hint="With the country code, e.g. +965 5000 0000">
                  <input
                    type="tel"
                    {...field('phone_1')}
                    pattern={PHONE_PATTERN}
                    title={PHONE_HINT}
                    autoComplete="tel"
                    required
                  />
                </Field>

                <Field label="Second phone number" optional>
                  <input
                    type="tel"
                    {...field('phone_2')}
                    pattern={PHONE_PATTERN}
                    title={PHONE_HINT}
                    placeholder="+965 6000 0000"
                  />
                </Field>
              </section>

              {/* Bottom left */}
              <section className="join-card">
                <h2>Chess details</h2>

                <Field label="FIDE ID" optional hint="Only if the player already has one.">
                  <input {...field('fide_id')} maxLength={20} inputMode="numeric" />
                </Field>

                
              </section>

              {/* Bottom right */}
              <section className="join-card">
                <h2>Confirm and register</h2>

                <label className="join-consent">
                  <input
                    type="checkbox"
                    checked={values.consent}
                    onChange={(event) => setField('consent', event.target.checked)}
                    required
                  />
                  <span>
                    I agree to the club rules and consent to KICA storing these details to
                    manage the player&apos;s membership.
                  </span>
                </label>

                {error && (
                  <p className="error" ref={errorRef} role="alert">
                    {error}
                  </p>
                )}

                <button type="submit" className="join-button join-submit" disabled={submitting}>
                  {submitting ? 'Sending...' : 'Register'}
                </button>
              </section>

              {/* Hidden from people (and screen readers); only bots fill it in */}
              <div className="join-trap" aria-hidden="true">
                <label>
                  Website
                  <input {...field('website')} tabIndex={-1} autoComplete="off" />
                </label>
              </div>
            </form>
          )}

          <p className="join-footer">
            Questions? Email us at <a href={`mailto:${CLUB_EMAIL}`}>{CLUB_EMAIL}</a>
          </p>
        </div>
      </div>
    </div>
  )
}

// A question: its label (with an "Optional" tag if needed), the box, and a hint underneath
// A question: its label, an "Optional" tag and a short hint on the same line, then the box
function Field({ label, optional = false, hint, children }) {
  return (
    <label className="join-field">
      <span className="join-label">
        {label}
        {optional && <span className="join-optional">Optional</span>}
        {hint && <span className="join-hint">{hint}</span>}
      </span>
      {children}
    </label>
  )
}

function ThankYou({ name, email, onRegisterAnother }) {
  return (
    <section className="join-card join-thanks">
      <div className="join-thanks-icon" aria-hidden="true">✓</div>
      <h2>Thank you!</h2>
      <p>
        We have received the registration for <strong>{name}</strong>.
      </p>
      <p>
        A confirmation email is on its way to <strong>{email}</strong> (please check your spam
        folder if you don&apos;t see it). Our team will review the registration and contact you
        soon.
      </p>

      <div className="join-whatsapp">
        <p>
          <strong>Join the KICA Members WhatsApp group</strong> for club news and updates. A
          group admin will approve your request.
        </p>

        <a
          className="button join-button join-whatsapp-button"
          href={WHATSAPP_GROUP_LINK}
          target="_blank"
          rel="noopener noreferrer"
        >
          Join our WhatsApp group
        </a>

        <p className="join-hint">Or scan this code with your phone&apos;s camera:</p>

        <div className="join-qr">
          <QRCodeSVG value={WHATSAPP_GROUP_LINK} size={200} />
        </div>
      </div>

      <button type="button" className="secondary join-button" onClick={onRegisterAnother}>
        Register another player
      </button>
    </section>
  )
}