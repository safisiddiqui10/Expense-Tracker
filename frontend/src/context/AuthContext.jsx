import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    api.me()
      .then(data => setUser(data))
      .catch(() => setUser(null))
  }, [])

  const login = (userData) => setUser(userData)
  const logout = () => api.logout().then(() => setUser(null))

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
