import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { auth } from '../api/auth'
import { AuthContext } from './auth'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userId, setUserId] = useState<string | null>(null)
  const [email, setEmail] = useState<string | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const bootstrapAuth = async () => {
      const storedUserId = localStorage.getItem('user_id')
      const storedEmail = localStorage.getItem('email')

      if (!storedUserId || !storedEmail) {
        setIsInitializing(false)
        return
      }

      const hasSession = await auth.hasActiveSession()
      if (hasSession) {
        setIsAuthenticated(true)
        setUserId(storedUserId)
        setEmail(storedEmail)
      } else {
        localStorage.removeItem('user_id')
        localStorage.removeItem('email')
      }

      setIsInitializing(false)
    }

    void bootstrapAuth()
  }, [])

  const login = async (emailInput: string, passwordInput: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await auth.login({ email: emailInput, password: passwordInput })
      localStorage.setItem('user_id', response.id)
      localStorage.setItem('email', response.email)
      setIsAuthenticated(true)
      setUserId(response.id)
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
      await auth.signup({ email: emailInput, password: passwordInput })

      const loginResponse = await auth.login({ email: emailInput, password: passwordInput })
      localStorage.setItem('user_id', loginResponse.id)
      localStorage.setItem('email', loginResponse.email)
      setIsAuthenticated(true)
      setUserId(loginResponse.id)
      setEmail(loginResponse.email)
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
        isInitializing,
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
