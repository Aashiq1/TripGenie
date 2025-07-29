import axios, { AxiosResponse } from 'axios'
import { User } from '../stores/authStore'

const API_BASE_URL = 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const authData = localStorage.getItem('auth-storage')
  if (authData) {
    try {
      const { state } = JSON.parse(authData)
      if (state?.tokens?.access_token) {
        config.headers.Authorization = `Bearer ${state.tokens.access_token}`
      }
    } catch (error) {
      console.error('Error parsing auth data:', error)
    }
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const authData = localStorage.getItem('auth-storage')
        if (authData) {
          const { state } = JSON.parse(authData)
          if (state?.tokens?.refresh_token) {
            const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
              refresh_token: state.tokens.refresh_token,
            })

            const { access_token, token_type, expires_in } = refreshResponse.data
            
            // Update stored tokens
            const updatedAuth = {
              ...JSON.parse(authData),
              state: {
                ...state,
                tokens: {
                  ...state.tokens,
                  access_token,
                  token_type,
                  expires_in,
                }
              }
            }
            localStorage.setItem('auth-storage', JSON.stringify(updatedAuth))

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return api(originalRequest)
          }
        }
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        localStorage.removeItem('auth-storage')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new FormData()
    formData.append('username', email) // FastAPI OAuth2PasswordRequestForm expects 'username'
    formData.append('password', password)
    
    const response: AxiosResponse = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (email: string, password: string, fullName: string) => {
    const response: AxiosResponse = await api.post('/auth/register', {
      email,
      password,
      fullName,
    })
    return response.data
  },

  refresh: async (refreshToken: string) => {
    const response: AxiosResponse = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  getProfile: async (): Promise<User> => {
    const response: AxiosResponse = await api.get('/auth/me')
    return response.data
  },

  getTrips: async () => {
    const response: AxiosResponse = await api.get('/auth/trips')
    return response.data
  },
}

// Trip API
export const tripAPI = {
  createTrip: async (tripData: any) => {
    const response: AxiosResponse = await api.post('/inputs/group', tripData)
    return response.data
  },

  joinTrip: async (groupCode: string, userInput: any) => {
    const response: AxiosResponse = await api.post('/inputs/user', {
      ...userInput,
      group_code: groupCode,
    })
    return response.data
  },

  getTripDetails: async (groupCode: string) => {
    const response: AxiosResponse = await api.get(`/trip/${groupCode}`)
    return response.data
  },

  planTrip: async (groupCode: string) => {
    const response: AxiosResponse = await api.post(`/trip/${groupCode}/plan`)
    return response.data
  },

  updateTrip: async (groupCode: string, updates: any) => {
    const response: AxiosResponse = await api.put(`/trip/${groupCode}`, updates)
    return response.data
  },

  getTripPlan: async (groupCode: string) => {
    const response: AxiosResponse = await api.get(`/trip/${groupCode}/plan`)
    return response.data
  },

  getTripPreview: async (groupCode: string) => {
    const response: AxiosResponse = await api.get(`/trip/${groupCode}/preview`)
    return response.data
  },
}

export default api 