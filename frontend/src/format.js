function pad(number) {
  return String(number).padStart(2, '0')
}

// Amounts arrive from the API as exact text such as "5.000", so they are shown as they are
export function kwd(amount) {
  return `${amount} KWD`
}

// "2026-10-16" -> "16 Oct 2026"
export function formatDate(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// "2026-10-01" -> "October 2026"
export function monthLabel(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-GB', {
    month: 'long',
    year: 'numeric',
  })
}

// Today as "2026-10-31", the format a date picker uses
export function today() {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

// This month as "2026-10", the format a month picker uses
export function currentMonth() {
  return today().slice(0, 7)
}


// "2026-10-16" -> "Fri 16 Oct 2026"
export function formatDay(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}