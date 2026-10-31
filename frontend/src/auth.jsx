import { createContext, useContext, useEffect, useState } from 'react'
import { api } from './api'
export const MIN_PASSWORD_LENGTH = 12

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // When the app opens, ask the backend whether the browser already has a valid session
  useEffect(() => {
    api('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function logIn(email, password, rememberMe) {
    await api('/auth/login', {
      method: 'POST',
      body: { email, password, remember_me: rememberMe },
    })
    setUser(await api('/auth/me'))
  }

  async function logOut() {
    await api('/auth/logout', { method: 'POST' })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, logIn, logOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}