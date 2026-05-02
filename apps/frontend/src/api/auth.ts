import client from './client'
import axios from 'axios'

export interface SignUpRequest {
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  id: string
  email: string
}

const formatApiErrorMessage = (error: unknown, fallback: string): string => {
  if (!axios.isAxiosError(error)) {
    return fallback
  }

  if (!error.response) {
    return 'Cannot reach API server. Please ensure backend is running on http://localhost:8000.'
  }

  const detail = error.response.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const firstDetail = detail[0]
    if (firstDetail && typeof firstDetail.msg === 'string') {
      return firstDetail.msg
    }
  }

  return fallback
}

export const auth = {
  signup: async (data: SignUpRequest): Promise<AuthResponse> => {
    try {
      const response = await client.post('/auth/signup', {
        email: data.email.trim().toLowerCase(),
        password: data.password,
      })
      return response.data
    } catch (error) {
      const message = formatApiErrorMessage(error, 'Signup failed')
      throw new Error(message, { cause: error })
    }
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    try {
      const response = await client.post('/auth/login', {
        email: data.email.trim().toLowerCase(),
        password: data.password,
      })
      return response.data
    } catch (error) {
      const message = formatApiErrorMessage(error, 'Login failed')
      throw new Error(message, { cause: error })
    }
  },

  logout: async (): Promise<void> => {
    await client.post('/auth/logout')
  },

  hasActiveSession: async (): Promise<boolean> => {
    try {
      await client.get('/auth/sessions')
      return true
    } catch {
      return false
    }
  },

  resetPassword: async (email: string): Promise<{ message: string }> => {
    const response = await client.post('/auth/password-reset-request', {
      email: email.trim().toLowerCase(),
    })
    return response.data
  },

  confirmReset: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await client.post('/auth/password-reset-confirm', {
      token,
      new_password: newPassword,
    })
    return response.data
  },
}
