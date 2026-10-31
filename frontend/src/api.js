// Every request to the backend goes through here, so errors are handled the same way everywhere
export class ApiError extends Error {
  constructor(status, message, details) {
    super(message)
    this.status = status
    this.details = details
  }
}

export async function api(path, { method = 'GET', body, params } = {}) {
  let url = `/api${path}`

  if (params) {
    url += `?${new URLSearchParams(params)}`
  }

  const response = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })

  // 204 means "done, nothing to send back"
  if (response.status === 204) {
    return null
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(data), data)
  }

  return data
}

function errorMessage(data) {
  if (!data || !data.detail) {
    return 'Something went wrong. Please try again.'
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  // Validation errors (422) arrive as a list: show the first one in plain words
  const first = data.detail[0]
  const field = first.loc[first.loc.length - 1]
  return `${field}: ${first.msg}`
}