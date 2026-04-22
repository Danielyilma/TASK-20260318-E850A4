import { defineStore } from 'pinia'
import * as activityService from '../services/activity.service'
import { useAuthStore } from './auth'

export const useActivityStore = defineStore('activities', {
  state: () => ({
    items: [],
    total: 0,
    page: 1,
    perPage: 20,
    pages: 0,
    loading: false,
    error: null,
    loaded: false,
  }),
  actions: {
    async fetchActivities(params = {}) {
      const auth = useAuthStore()
      if (!auth.isAuthenticated) {
        this.items = []
        this.total = 0
        this.pages = 0
        this.loaded = false
        return
      }

      this.loading = true
      this.error = null
      try {
        const data = await activityService.listActivities({
          page: params.page ?? 1,
          per_page: params.per_page ?? 20,
          is_active: params.is_active,
          search: params.search,
        })
        this.items = data.items ?? []
        this.total = data.total ?? 0
        this.page = data.page ?? 1
        this.perPage = data.per_page ?? 20
        this.pages = data.pages ?? 0
        this.loaded = true
      } catch (e) {
        this.items = []
        this.error = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load activities'
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    clear() {
      this.items = []
      this.total = 0
      this.page = 1
      this.perPage = 20
      this.pages = 0
      this.loading = false
      this.error = null
      this.loaded = false
    },
  },
})
