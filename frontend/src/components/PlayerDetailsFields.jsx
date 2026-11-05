import { useEffect, useState } from 'react'
import { api } from '../api'
import { today } from '../format'

// The demo values the migrations gave to existing players
export const DEMO_VALUES = {
  phone_1: '+965 0000 0000',
  email: 'update.me@example.com',
  parent_name: 'To be updated',
  date_of_birth: '2000-01-01',
  country: 'To be updated',
}

// True if any details are still demo values, or gender hasn't been set yet
export function hasDemoDetails(player) {
  return (
    !player.gender ||
    Object.entries(DEMO_VALUES).some(([field, demo]) => player[field] === demo)
  )
}

// 'female' -> 'Female'
export function genderLabel(gender) {
  return gender ? gender.charAt(0).toUpperCase() + gender.slice(1) : null
}

// The countries to choose from (India and Kuwait first), loaded from the backend
export function useCountries() {
  const [countries, setCountries] = useState([])

  useEffect(() => {
    api('/countries/')
      .then(setCountries)
      .catch(() => {})
  }, [])

  return countries
}

// How many countries the backend puts at the top (India, Kuwait)
const PINNED_COUNT = 2

// The options inside a country dropdown: a prompt, the pinned countries, a line, then A–Z
export function CountryOptions({ countries }) {
  return (
    <>
      <option value="" disabled>
        Choose a country
      </option>
      {countries.slice(0, PINNED_COUNT).map((country) => (
        <option key={country} value={country}>
          {country}
        </option>
      ))}
      {countries.length > PINNED_COUNT && <option disabled>──────────</option>}
      {countries.slice(PINNED_COUNT).map((country) => (
        <option key={country} value={country}>
          {country}
        </option>
      ))}
    </>
  )
}

// Starting values for the form.
// No player = a new player. Inputs can't show null, so null becomes ''.
// A demo country ("To be updated") starts empty, so the Exec must choose a real one.
export function formValues(player) {
  return {
    name: player?.name ?? '',
    parent_name: player?.parent_name ?? '',
    email: player?.email ?? '',
    phone_1: player?.phone_1 ?? '+965 ',
    phone_2: player?.phone_2 ?? '',
    date_of_birth: player?.date_of_birth ?? '',
    gender: player?.gender ?? '',
    country: player && player.country !== DEMO_VALUES.country ? player.country : '',
    fide_id: player?.fide_id ?? '',
    joined_on: player ? player.joined_on ?? '' : today(),
  }
}

// What gets sent to the API
export function requestBody(values) {
  const body = { ...values, gender: values.gender || null }

  // Some older players have no joined date. Leave it out instead of sending ''.
  if (!body.joined_on) {
    delete body.joined_on
  }

  return body
}

export const PHONE_PATTERN = '\\+?[0-9 \\-]{7,30}'
export const PHONE_HINT = 'Numbers with the country code, e.g. +965 5000 0000'

export default function PlayerDetailsFields({ values, onChange, isNew, kicaId }) {
  const countries = useCountries()

  // Gives an input its value and what to do when it changes
  function field(name) {
    return {
      value: values[name],
      onChange: (event) => onChange(name, event.target.value),
    }
  }

  return (
    <>
      <div className="form-row">
        <label>
          KICA ID (automatic)
          <input value={kicaId ?? 'Loading...'} readOnly tabIndex={-1} />
        </label>

        <label>
          Full name
          <input {...field('name')} maxLength={100} required />
        </label>

        <label>
          Parent name
          <input {...field('parent_name')} maxLength={100} required />
        </label>
      </div>

      <div className="form-row">
        <label>
          Email
          <input type="email" {...field('email')} maxLength={255} required />
        </label>
      </div>

      <div className="form-row">
        <label>
          Whatsapp Number
          <input
            type="tel"
            {...field('phone_1')}
            pattern={PHONE_PATTERN}
            title={PHONE_HINT}
            placeholder="+965 5000 0000"
            required
          />
        </label>

        <label>
          Phone 2 (optional)
          <input
            type="tel"
            {...field('phone_2')}
            pattern={PHONE_PATTERN}
            title={PHONE_HINT}
            placeholder="+965 6000 0000"
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Date of birth
          <input type="date" {...field('date_of_birth')} max={today()} required />
        </label>

        <label>
          Gender
          <select {...field('gender')} required>
            <option value="" disabled>
              Choose...
            </option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          Country
          <select {...field('country')} required>
            <CountryOptions countries={countries} />
          </select>
        </label>
      </div>

      <div className="form-row">
        <label>
          FIDE ID (optional)
          <input {...field('fide_id')} maxLength={20} />
        </label>

        <label>
          Joined on
          <input type="date" {...field('joined_on')} max={today()} required={isNew} />
        </label>
      </div>
    </>
  )
}