import { defineStore } from 'pinia'

export const useNetworkStore = defineStore('network', {
  state: () => ({
    online: typeof navigator === 'undefined' ? true : navigator.onLine,
    initialized: false,
  }),
  actions: {
    setOnline(value) {
      this.online = Boolean(value)
    },
    init() {
      if (this.initialized || typeof window === 'undefined') return
      this.initialized = true
      this.online = navigator.onLine
      window.addEventListener('online', () => this.setOnline(true))
      window.addEventListener('offline', () => this.setOnline(false))
    },
  },
})
