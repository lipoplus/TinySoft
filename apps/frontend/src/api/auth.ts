import client from './client'

export interface SignUpRequest {
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  user_id: string
  email: string
  session_token: string
}

export const auth = {
  signup: async (data: SignUpRequest): Promise<AuthResponse> => {
    const response = await client.post('/auth/signup', data)
    return response.data
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await client.post('/auth/login', data)
    return response.data
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
