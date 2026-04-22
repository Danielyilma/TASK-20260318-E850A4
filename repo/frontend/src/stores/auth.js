import { defineStore } from 'pinia'
import * as authService from '../services/auth.service'

const TOKEN_KEY = 'arfamp_access_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null,
    user: null,
    loading: false,
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    restoreSession() {
      const token = localStorage.getItem(TOKEN_KEY)
      this.accessToken = token
    },
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const data = await authService.login(username, password)
        this.accessToken = data.access_token
        this.user = data.user
        localStorage.setItem(TOKEN_KEY, data.access_token)
        return data
      } catch (e) {
        this.accessToken = null
        this.user = null
        localStorage.removeItem(TOKEN_KEY)
        this.error = e?.response?.data?.error?.message ?? e.message ?? 'Login failed'
        throw e
      } finally {
        this.loading = false
      }
    },
    async logout() {
      this.loading = true
      this.error = null
      try {
        await authService.logout()
      } catch (e) {
        // Still clear local session even if server rejects an expired token edge case.
        this.error = e?.response?.data?.error?.message ?? e.message ?? null
      } finally {
        this.accessToken = null
        this.user = null
        localStorage.removeItem(TOKEN_KEY)
        this.loading = false
      }
    },
    async loadMe() {
      if (!this.accessToken) return
      this.loading = true
      this.error = null
      try {
        this.user = await authService.fetchMe()
      } catch (e) {
        this.error = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load profile'
        this.accessToken = null
        this.user = null
        localStorage.removeItem(TOKEN_KEY)
        throw e
      } finally {
        this.loading = false
      }
    },
  },
})
