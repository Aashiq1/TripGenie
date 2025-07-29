import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'

export interface User {
  id: string
  email: string
  fullName: string
  createdAt: string
}

interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, fullName: string) => Promise<boolean>
  logout: () => void
  refreshToken: () => Promise<boolean>
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          // Clear any existing auth state first
          set({ user: null, tokens: null })
          
          const response = await authAPI.login(email, password)
          const { user, access_token, refresh_token, token_type, expires_in } = response
          
          set({ 
            user,
            tokens: { access_token, refresh_token, token_type, expires_in },
            isLoading: false 
          })
          
          toast.success(`Welcome back, ${user.fullName}!`)
          return true
        } catch (error: any) {
          console.error('Login error:', error)
          toast.error(error.response?.data?.detail || 'Login failed')
          set({ isLoading: false })
          return false
        }
      },

      register: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true })
        try {
          // Clear any existing auth state first
          set({ user: null, tokens: null })
          
          const response = await authAPI.register(email, password, fullName)
          const { user, access_token, refresh_token, token_type, expires_in } = response
          
          set({ 
            user,
            tokens: { access_token, refresh_token, token_type, expires_in },
            isLoading: false 
          })
          
          toast.success(`Welcome to TripGenie, ${user.fullName}!`)
          return true
        } catch (error: any) {
          console.error('Register error:', error)
          toast.error(error.response?.data?.detail || 'Registration failed')
          set({ isLoading: false })
          return false
        }
      },

      logout: () => {
        set({ user: null, tokens: null })
        toast.success('Logged out successfully')
      },

      refreshToken: async () => {
        const { tokens } = get()
        if (!tokens?.refresh_token) return false

        try {
          const response = await authAPI.refresh(tokens.refresh_token)
          const { access_token, token_type, expires_in } = response
          
          set({ 
            tokens: { 
              ...tokens, 
              access_token, 
              token_type, 
              expires_in 
            }
          })
          
          return true
        } catch (error: any) {
          console.error('Token refresh error:', error)
          // If refresh fails, logout the user
          get().logout()
          return false
        }
      },

      clearAuth: () => {
        set({ user: null, tokens: null, isLoading: false })
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        tokens: state.tokens 
      }),
    }
  )
)

// Listen for storage changes across tabs to handle cross-tab authentication
if (typeof window !== 'undefined') {
  const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  
  window.addEventListener('storage', (e) => {
    if (e.key === 'auth-storage' && e.newValue) {
      try {
        const newAuth = JSON.parse(e.newValue)
        const currentAuth = useAuthStore.getState()
        
        // If a different user logged in on another tab
        if (newAuth.state?.user?.id !== currentAuth.user?.id) {
          if (isDevelopment) {
            // In development: immediately refresh for easier testing
            console.log('Different user detected across tabs, refreshing...')
            window.location.reload()
          } else {
            // In production: show a banner/notification instead of forcing refresh
            console.log('Different user detected across tabs, clearing auth...')
            useAuthStore.getState().clearAuth()
            // You could show a toast notification here instead of silent clear
            // toast.info('Account changed in another tab. Please log in again.')
          }
        }
      } catch (error) {
        console.error('Error handling storage change:', error)
      }
    } else if (e.key === 'auth-storage' && e.newValue === null) {
      // User logged out on another tab - always clear auth
      console.log('Logout detected across tabs, clearing auth...')
      useAuthStore.getState().clearAuth()
    }
  })
} 