import axios from 'axios'
import { auth } from '../firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - attach Firebase ID token
apiClient.interceptors.request.use(
  async (config) => {
    const user = auth.currentUser

    // Debug logging
    console.log(`[API] Request to: ${config.url}`)
    console.log(`[API] User authenticated:`, !!user)

    if (user) {
      try {
        const token = await user.getIdToken()
        config.headers.Authorization = `Bearer ${token}`
        console.log(`[API] Token attached:`, token.substring(0, 20) + '...')
      } catch (error) {
        console.error('[API] Failed to get token:', error)
        throw error
      }
    } else {
      console.warn('[API] No authenticated user - request will fail if auth is required')
    }

    return config
  },
  (error) => {
    console.error('[API] Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred'

      console.error(`[API] Error ${error.response.status}:`, message)
      console.error(`[API] Failed request:`, originalRequest.url)

      if (error.response.status === 401) {
        // Unauthorized - try to refresh token once
        if (!originalRequest._retry) {
          originalRequest._retry = true

          console.log('[API] 401 error - attempting token refresh...')

          const user = auth.currentUser
          if (user) {
            try {
              // Force token refresh
              const token = await user.getIdToken(true)
              originalRequest.headers.Authorization = `Bearer ${token}`
              console.log('[API] Token refreshed, retrying request...')
              return apiClient(originalRequest)
            } catch (refreshError) {
              console.error('[API] Token refresh failed:', refreshError)
            }
          }
        }

        // If retry failed or no user, redirect to login
        console.log('[API] Redirecting to login...')
        window.location.href = '/login'
      }

      return Promise.reject(new Error(message))
    } else if (error.request) {
      // Request made but no response
      console.error('[API] No response from server')
      return Promise.reject(new Error('No response from server'))
    } else {
      // Something else happened
      console.error('[API] Request setup error:', error.message)
      return Promise.reject(error)
    }
  }
)

export default apiClient
