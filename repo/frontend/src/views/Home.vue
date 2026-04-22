<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useHealthStore } from '../stores/health'
import { useAuthStore } from '../stores/auth'

const health = useHealthStore()
const auth = useAuthStore()
const showReviews = computed(() => auth.user?.role === 'reviewer')
const showFunding = computed(() =>
  auth.user?.role === 'financial_admin' || auth.user?.role === 'system_admin',
)
const showAdminConsole = computed(() => auth.user?.role === 'system_admin')

onMounted(async () => {
  health.loadHealth()
  auth.restoreSession()
  if (auth.accessToken && !auth.user) {
    try {
      await auth.loadMe()
    } catch {
      /* ignore */
    }
  }
})
</script>

<template>
  <section class="home">
    <h1>Activity Registration Platform</h1>
    <p class="lede">Local scaffold — backend health is read from the live API.</p>
    <p class="lede">
      <RouterLink to="/login">Sign in</RouterLink>
      , then open
      <RouterLink to="/activities">Activities</RouterLink>
      to manage records against the live API.
      <template v-if="auth.isAuthenticated">
        <span v-if="showReviews"> · <RouterLink to="/reviews">Reviewer dashboard</RouterLink></span>
        <span v-if="showFunding"> · <RouterLink to="/funding">Funding</RouterLink></span>
        <span v-if="showAdminConsole"> · <RouterLink to="/admin/console">Admin console</RouterLink></span>
      </template>
    </p>

    <div class="card">
      <div class="row">
        <span class="label">API status</span>
        <span v-if="health.loading" class="value muted">Checking…</span>
        <span v-else-if="health.status" class="value ok">{{ health.status }}</span>
        <span v-else class="value err">unavailable</span>
      </div>
      <p v-if="health.error" class="error" role="alert">{{ health.error }}</p>
      <button type="button" class="btn" :disabled="health.loading" @click="health.loadHealth()">
        Refresh health
      </button>
    </div>
  </section>
</template>

<style scoped>
.home {
  max-width: 720px;
}
h1 {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
}
.lede {
  margin: 0 0 1.5rem;
  color: #4b5563;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1.25rem;
  background: #fafafa;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
.label {
  font-weight: 600;
  color: #111827;
}
.value.ok {
  color: #047857;
  font-weight: 600;
  text-transform: uppercase;
}
.value.err {
  color: #b91c1c;
  font-weight: 600;
}
.value.muted {
  color: #6b7280;
}
.error {
  color: #b91c1c;
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
.btn {
  cursor: pointer;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.5rem 0.9rem;
  font-weight: 600;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn:not(:disabled):hover {
  border-color: #9ca3af;
}
</style>
