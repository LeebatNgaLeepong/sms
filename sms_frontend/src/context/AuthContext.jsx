import { createContext, useContext, useState, useCallback } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('sms_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = useCallback(async (username, password) => {
    const res = await api.post('/auth/login/', { username, password })
    const { access, refresh, user: userData } = res.data
    localStorage.setItem('sms_tokens', JSON.stringify({ access, refresh }))
    localStorage.setItem('sms_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }, [])

  const logout = useCallback(async () => {
    try {
      const tokens = JSON.parse(localStorage.getItem('sms_tokens') || '{}')
      if (tokens.refresh) {
        await api.post('/auth/logout/', { refresh: tokens.refresh })
      }
    } catch {
      // Silently handle logout errors
    } finally {
      localStorage.removeItem('sms_tokens')
      localStorage.removeItem('sms_user')
      setUser(null)
    }
  }, [])

  const isAdmin = user?.role === 'admin'
  const isTeacher = user?.role === 'teacher'
  const isStudent = user?.role === 'student'

  return (
    <AuthContext.Provider value={{ user, login, logout, isAdmin, isTeacher, isStudent }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
