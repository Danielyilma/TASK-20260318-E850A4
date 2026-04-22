<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getActivity } from '../services/activity.service'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const activity = ref(null)
const loading = ref(false)
const error = ref('')

const activityId = computed(() => String(route.params.id ?? ''))
const showRegister = computed(() => auth.user?.role === 'applicant')

async function load() {
  loading.value = true
  error.value = ''
  try {
    activity.value = await getActivity(activityId.value)
  } catch (e) {
    activity.value = null
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load activity'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await load()
})

watch(activityId, async () => {
  await load()
})

function formatMoney(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Activity</h1>
        <p class="subhead mono" v-if="activity">{{ activity.id }}</p>
      </div>
      <div class="header-actions">
        <RouterLink
          v-if="showRegister && activity"
          class="btn primary"
          :to="{ name: 'registration-new', query: { activity_id: activity.id } }"
        >
          Register
        </RouterLink>
        <button type="button" class="btn secondary" :disabled="loading" @click="load">Refresh</button>
      </div>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>
    <p v-if="loading" class="muted">Loading…</p>

    <div v-if="!loading && activity" class="card">
      <div class="grid">
        <div>
          <div class="label">Name</div>
          <div class="value">{{ activity.name }}</div>
        </div>
        <div>
          <div class="label">Budget</div>
          <div class="value num">{{ formatMoney(activity.budget) }}</div>
        </div>
        <div class="full">
          <div class="label">Description</div>
          <div class="value">{{ activity.description || '—' }}</div>
        </div>
        <div>
          <div class="label">Deadline</div>
          <div class="value mono">{{ activity.deadline }}</div>
        </div>
        <div>
          <div class="label">Active</div>
          <div class="value">{{ activity.is_active ? 'Yes' : 'No' }}</div>
        </div>
        <div>
          <div class="label">Created</div>
          <div class="value mono">{{ activity.created_at }}</div>
        </div>
        <div>
          <div class="label">Updated</div>
          <div class="value mono">{{ activity.updated_at }}</div>
        </div>
      </div>
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
.header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
h1 {
  margin: 0 0 0.35rem;
}
.subhead {
  margin: 0;
  color: #6b7280;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}
.full {
  grid-column: 1 / -1;
}
.label {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 700;
  margin-bottom: 0.25rem;
}
.value {
  color: #111827;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.95rem;
}
.num {
  font-variant-numeric: tabular-nums;
}
.btn {
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.55rem 0.85rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  display: inline-block;
}
.btn.primary {
  background: #2563eb;
  border-color: #1d4ed8;
  color: #fff;
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
}
</style>
