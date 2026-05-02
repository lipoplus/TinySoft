import { createContext } from 'react'

export interface AuthContextType {
  isAuthenticated: boolean
  userId: string | null
  email: string | null
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
  error: string | null
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)
