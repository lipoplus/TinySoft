import { useState } from 'react'
import type { ReactNode } from 'react'
import { auth } from '../api/auth'
import { AuthContext } from './auth'

interface AuthProviderProps {
  children: ReactNode
}

function initializeAuth() {
  const token = localStorage.getItem('session_token')
  const storedUserId = localStorage.getItem('user_id')
  const storedEmail = localStorage.getItem('email')

  return {
    isAuthenticated: Boolean(token && storedUserId && storedEmail),
    userId: storedUserId,
    email: storedEmail,
  }
}

export function AuthProvider({ children }: AuthProviderProps) {
  const initialAuth = initializeAuth()
  const [isAuthenticated, setIsAuthenticated] = useState(initialAuth.isAuthenticated)
  const [userId, setUserId] = useState<string | null>(initialAuth.userId)
  const [email, setEmail] = useState<string | null>(initialAuth.email)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = async (emailInput: string, passwordInput: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await auth.login({ email: emailInput, password: passwordInput })
      localStorage.setItem('session_token', response.session_token)
      localStorage.setItem('user_id', response.user_id)
      localStorage.setItem('email', response.email)
      setIsAuthenticated(true)
      setUserId(response.user_id)
      setEmail(response.email)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const signup = async (emailInput: string, passwordInput: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await auth.signup({ email: emailInput, password: passwordInput })
      localStorage.setItem('session_token', response.session_token)
      localStorage.setItem('user_id', response.user_id)
      localStorage.setItem('email', response.email)
      setIsAuthenticated(true)
      setUserId(response.user_id)
      setEmail(response.email)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Signup failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await auth.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      localStorage.removeItem('session_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('email')
      setIsAuthenticated(false)
      setUserId(null)
      setEmail(null)
      setIsLoading(false)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        userId,
        email,
        login,
        signup,
        logout,
        isLoading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
