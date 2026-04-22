<script setup>
import { onMounted, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useActivityStore } from '../stores/activity'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const activities = useActivityStore()

async function refresh() {
  await activities.fetchActivities()
}

async function signOut() {
  await auth.logout()
  activities.clear()
  await router.push({ name: 'login' })
}

onMounted(async () => {
  await activities.fetchActivities()
})

watch(
  () => auth.isAuthenticated,
  async (isAuthed) => {
    if (!isAuthed) {
      activities.clear()
    } else {
      await activities.fetchActivities()
    }
  },
)

function formatMoney(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function goDetail(id) {
  router.push({ name: 'activity-detail', params: { id } })
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Activities</h1>
        <p class="subhead">Data is loaded from the backend API (no mocked HTTP responses in the app).</p>
      </div>
      <div class="header-actions">
        <button type="button" class="btn secondary" @click="signOut">Sign out</button>
        <RouterLink class="btn" to="/activities/new">New activity</RouterLink>
      </div>
    </header>

    <div class="card">
      <div class="toolbar">
        <div v-if="auth.user" class="who">
          Signed in as <strong>{{ auth.user.username }}</strong>
          <span class="pill">{{ auth.user.role }}</span>
        </div>
        <button type="button" class="btn secondary" :disabled="activities.loading" @click="refresh">Refresh</button>
      </div>

      <p v-if="activities.error" class="err" role="alert">{{ activities.error }}</p>

      <div v-if="activities.loading" class="muted">Loading activities…</div>

      <table v-else class="table" aria-label="Activities">
        <thead>
          <tr>
            <th>Name</th>
            <th>Deadline</th>
            <th>Budget</th>
            <th>Active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="activities.items.length === 0">
            <td colspan="5" class="muted">No activities yet. Create one to get started.</td>
          </tr>
          <tr v-for="a in activities.items" :key="a.id">
            <td class="name">{{ a.name }}</td>
            <td class="mono">{{ a.deadline }}</td>
            <td class="num">{{ formatMoney(a.budget) }}</td>
            <td>{{ a.is_active ? 'Yes' : 'No' }}</td>
            <td class="actions">
              <button type="button" class="linkish" @click="goDetail(a.id)">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}
h1 {
  margin: 0 0 0.35rem;
}
.subhead {
  margin: 0;
  color: #4b5563;
}
.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}
.who {
  color: #111827;
}
.pill {
  margin-left: 0.5rem;
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-size: 0.85rem;
  color: #374151;
}
.table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
th,
td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  text-align: left;
  vertical-align: top;
}
th {
  font-size: 0.85rem;
  color: #374151;
  background: #f9fafb;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.9rem;
}
.actions {
  text-align: right;
  white-space: nowrap;
}
.linkish {
  border: none;
  background: transparent;
  color: #2563eb;
  font-weight: 700;
  cursor: pointer;
  padding: 0.15rem 0.25rem;
}
.linkish:hover {
  text-decoration: underline;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.55rem 0.85rem;
  font-weight: 700;
  text-decoration: none;
  color: #111827;
  cursor: pointer;
}
.btn.secondary {
  background: #fff;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.muted {
  color: #6b7280;
}
.err {
  color: #b91c1c;
  margin: 0.25rem 0 0;
}
</style>
