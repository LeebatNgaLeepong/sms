import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — attach access token
api.interceptors.request.use(
  (config) => {
    const tokens = JSON.parse(localStorage.getItem('sms_tokens') || '{}')
    if (tokens.access) {
      config.headers.Authorization = `Bearer ${tokens.access}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const tokens = JSON.parse(localStorage.getItem('sms_tokens') || '{}')

      if (tokens.refresh) {
        try {
          const res = await axios.post('/api/auth/refresh/', {
            refresh: tokens.refresh,
          })
          const newTokens = {
            access: res.data.access,
            refresh: res.data.refresh || tokens.refresh,
          }
          localStorage.setItem('sms_tokens', JSON.stringify(newTokens))
          originalRequest.headers.Authorization = `Bearer ${newTokens.access}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem('sms_tokens')
          localStorage.removeItem('sms_user')
          window.location.href = '/login'
        }
      } else {
        localStorage.removeItem('sms_tokens')
        localStorage.removeItem('sms_user')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api
