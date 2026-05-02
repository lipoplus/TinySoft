import axios from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
})

export default client
