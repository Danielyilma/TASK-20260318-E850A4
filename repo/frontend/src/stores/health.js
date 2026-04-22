import { defineStore } from 'pinia'
import { fetchHealth } from '../services/api'

export const useHealthStore = defineStore('health', {
  state: () => ({
    status: null,
    loading: false,
    error: null,
  }),
  actions: {
    async loadHealth() {
      this.loading = true
      this.error = null
      try {
        const data = await fetchHealth()
        this.status = data.status ?? null
      } catch (e) {
        this.status = null
        this.error = e?.response?.data?.error?.message ?? e.message ?? 'Unknown error'
      } finally {
        this.loading = false
      }
    },
  },
})
