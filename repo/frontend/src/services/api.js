import axios from 'axios'

function resolveBaseUrl() {
  const fromEnv = import.meta.env.VITE_API_BASE_URL
  if (fromEnv) {
    return fromEnv.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location
    return `${protocol}//${hostname}:8000/api/v1`
  }
  return 'http://localhost:8000/api/v1'
}

export const apiClient = axios.create({
  baseURL: resolveBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('arfamp_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  async (response) => {
    try {
      const { useNetworkStore } = await import('../stores/network.js')
      useNetworkStore().setOnline(true)
    } catch {
      /* ignore in tests without active pinia */
    }
    return response
  },
  async (error) => {
    const status = error.response?.status
    const reqUrl = String(error.config?.url ?? '')
    if (!error.response) {
      try {
        const { useNetworkStore } = await import('../stores/network.js')
        useNetworkStore().setOnline(false)
      } catch {
        /* ignore */
      }
    }
    if (status === 401 && !reqUrl.includes('/auth/login')) {
      localStorage.removeItem('arfamp_access_token')
      try {
        const { default: router } = await import('../router/index.js')
        if (router.currentRoute.value.name !== 'login') {
          await router.push({
            name: 'login',
            query: { redirect: router.currentRoute.value.fullPath },
          })
        }
      } catch {
        window.location.assign('/login')
      }
    } else if (status && status >= 400 && status !== 401) {
      const body = error.response?.data
      const code = body?.error?.code
      const message = body?.error?.message ?? error.message ?? 'Request failed'
      try {
        const { useToastStore } = await import('../stores/toast.js')
        useToastStore().push({
          title: code || `HTTP ${status}`,
          message,
          variant: 'error',
        })
      } catch {
        /* ignore toast failures (e.g. tests without pinia on window) */
      }
    }
    return Promise.reject(error)
  },
)

export async function fetchHealth() {
  const { data } = await apiClient.get('/health')
  return data
}
