<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import AppToast from './components/AppToast.vue'
import { useAuthStore } from './stores/auth'
import { useNetworkStore } from './stores/network'

const auth = useAuthStore()
const network = useNetworkStore()
auth.restoreSession()

const showAdminUsers = computed(() => auth.user?.role === 'system_admin')
const showAdminConsole = computed(() => auth.user?.role === 'system_admin')
const showReviews = computed(() => auth.user?.role === 'reviewer')
const showFunding = computed(() =>
  auth.user?.role === 'financial_admin' || auth.user?.role === 'system_admin',
)

onMounted(async () => {
  if (auth.accessToken && !auth.user) {
    try {
      await auth.loadMe()
    } catch {
      /* expired or revoked token */
    }
  }
})
</script>

<template>
  <div class="app-shell">
    <p v-if="!network.online" class="offline-banner" role="status">
      You are offline. Requests will fail until connection is restored.
    </p>
    <header class="top-nav">
      <div class="brand">ARFAMP</div>
      <nav class="links">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/activities">Activities</RouterLink>
        <RouterLink v-if="showReviews" to="/reviews">Reviews</RouterLink>
        <RouterLink v-if="showFunding" to="/funding">Funding</RouterLink>
        <RouterLink v-if="showAdminConsole" to="/admin/console">Admin console</RouterLink>
        <RouterLink v-if="showAdminUsers" to="/admin/users">Admin users</RouterLink>
        <RouterLink v-if="!auth.isAuthenticated" to="/login">Sign in</RouterLink>
      </nav>
    </header>
    <main class="content">
      <RouterView />
    </main>
    <AppToast />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: #111827;
  background: #ffffff;
}
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}
.brand {
  font-weight: 800;
  letter-spacing: 0.04em;
}
.links a {
  margin-right: 1rem;
  text-decoration: none;
  color: #1f2937;
  font-weight: 600;
}
.links a.router-link-active {
  color: #2563eb;
}
.content {
  flex: 1;
  padding: 1.5rem 1.25rem 2.5rem;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
}
.offline-banner {
  margin: 0;
  padding: 0.5rem 1rem;
  font-weight: 700;
  color: #92400e;
  background: #fef3c7;
  border-bottom: 1px solid #fcd34d;
  text-align: center;
}
</style>
