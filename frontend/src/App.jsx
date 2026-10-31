import { useEffect, useState } from 'react'

function App() {
  const [message, setMessage] = useState('Checking the connection...')

  useEffect(() => {
    fetch('/api/auth/me')
      .then((response) => {
        if (response.status === 401) {
          setMessage('Connected to the API. You are not logged in yet.')
        } else if (response.ok) {
          setMessage('Connected to the API and logged in.')
        } else {
          setMessage(`The API replied with status ${response.status}`)
        }
      })
      .catch(() => setMessage('Could not reach the API. Is the backend running?'))
  }, [])

  return <h1>{message}</h1>
}

export default App