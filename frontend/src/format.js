// Amounts arrive from the API as exact text such as "5.000", so they are shown as they are
export function kwd(amount) {
  return `${amount} KWD`
}

// "2026-10-01" -> "October 2026"
export function monthLabel(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-GB', {
    month: 'long',
    year: 'numeric',
  })
}

// This month as "2026-10", the format a month picker uses
export function currentMonth() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  return `${now.getFullYear()}-${month}`
}