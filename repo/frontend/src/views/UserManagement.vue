<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import * as userService from '../services/user.service'

const loading = ref(false)
const creating = ref(false)
const error = ref('')
const page = ref({ items: [], total: 0, page: 1, per_page: 20, pages: 0 })

const createForm = reactive({
  username: '',
  password: '',
  role: 'applicant',
  id_number: '',
  contact_info: '',
})

const roles = [
  { value: 'applicant', label: 'Applicant' },
  { value: 'reviewer', label: 'Reviewer' },
  { value: 'financial_admin', label: 'Financial admin' },
  { value: 'system_admin', label: 'System admin' },
]

const canCreate = computed(() => {
  return createForm.username.trim().length >= 3 && createForm.password.length > 0 && !creating.value
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    page.value = await userService.listUsers({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load users'
  } finally {
    loading.value = false
  }
}

async function createUser() {
  creating.value = true
  error.value = ''
  try {
    const payload = {
      username: createForm.username.trim(),
      password: createForm.password,
      role: createForm.role,
    }
    if (createForm.id_number.trim()) payload.id_number = createForm.id_number.trim()
    if (createForm.contact_info.trim()) payload.contact_info = createForm.contact_info.trim()
    await userService.createUser(payload)
    createForm.username = ''
    createForm.password = ''
    createForm.id_number = ''
    createForm.contact_info = ''
    await load()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Create failed'
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>User management</h1>
        <p class="subhead">System administrators manage accounts via <code>GET/POST /api/v1/users</code>.</p>
      </div>
    </header>

    <div class="card">
      <h2>Create user</h2>
      <p class="muted">Password must be at least 8 characters with upper, lower, digit, and special character.</p>

      <div class="grid">
        <label class="field">
          <span>Username</span>
          <input v-model="createForm.username" autocomplete="off" />
        </label>
        <label class="field">
          <span>Password</span>
          <input v-model="createForm.password" type="password" autocomplete="new-password" />
        </label>
        <label class="field">
          <span>Role</span>
          <select v-model="createForm.role">
            <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </label>
        <label class="field">
          <span>ID number (optional)</span>
          <input v-model="createForm.id_number" autocomplete="off" />
        </label>
        <label class="field wide">
          <span>Contact info (optional)</span>
          <input v-model="createForm.contact_info" autocomplete="off" />
        </label>
      </div>

      <button type="button" class="btn primary" :disabled="!canCreate" @click="createUser">
        {{ creating ? 'Creating…' : 'Create user' }}
      </button>
    </div>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div v-if="loading" class="muted">Loading users…</div>

    <div v-else class="card table-card">
      <h2>Directory</h2>
      <table class="table" aria-label="Users">
        <thead>
          <tr>
            <th>Username</th>
            <th>Role</th>
            <th>Locked</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="page.items.length === 0">
            <td colspan="4" class="muted">No users returned.</td>
          </tr>
          <tr v-for="u in page.items" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.role }}</td>
            <td>{{ u.is_locked ? 'Yes' : 'No' }}</td>
            <td class="mono">{{ u.created_at }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page-header {
  margin-bottom: 1rem;
}
h1 {
  margin: 0 0 0.35rem;
}
h2 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}
.subhead {
  margin: 0;
  color: #4b5563;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
  margin-bottom: 1rem;
}
.table-card {
  background: #fff;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem 1rem;
  margin-bottom: 1rem;
}
.field.wide {
  grid-column: 1 / -1;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
input,
select {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.55rem 0.65rem;
  font: inherit;
  background: #fff;
}
.btn {
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.55rem 0.85rem;
  font-weight: 700;
  cursor: pointer;
}
.btn.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}
th,
td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  text-align: left;
}
th {
  font-size: 0.85rem;
  color: #374151;
  background: #f9fafb;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85rem;
}
.muted {
  color: #6b7280;
}
.err {
  color: #b91c1c;
  margin: 0.5rem 0;
}
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}
</style>
