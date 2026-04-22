import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [],
    seq: 0,
  }),
  actions: {
    push({ title, message, variant = 'error', ttlMs = 6000 }) {
      const id = ++this.seq
      this.items.push({ id, title, message, variant, ttlMs })
      if (ttlMs > 0 && typeof window !== 'undefined') {
        window.setTimeout(() => this.dismiss(id), ttlMs)
      }
      return id
    },
    dismiss(id) {
      this.items = this.items.filter((x) => x.id !== id)
    },
    clear() {
      this.items = []
    },
  },
})
