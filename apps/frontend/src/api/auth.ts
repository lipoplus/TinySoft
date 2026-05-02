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

export const auth = {
  signup: async (data: SignUpRequest): Promise<AuthResponse> => {
    try {
      const response = await client.post('/auth/signup', {
        email: data.email.trim().toLowerCase(),
        password: data.password,
      })
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail
        throw new Error(typeof detail === 'string' ? detail : 'Signup failed')
      }
      throw error
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
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail
        throw new Error(typeof detail === 'string' ? detail : 'Login failed')
      }
      throw error
    }
  },

  logout: async (): Promise<void> => {
    await client.post('/auth/logout')
  },

  resetPassword: async (email: string): Promise<{ message: string }> => {
    const response = await client.post('/auth/reset-password', { email })
    return response.data
  },

  confirmReset: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await client.post('/auth/reset-password/confirm', {
      token,
      new_password: newPassword,
    })
    return response.data
  },
}
