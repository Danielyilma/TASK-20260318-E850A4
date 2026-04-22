<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createActivity } from '../services/activity.service'
const router = useRouter()

const form = reactive({
  name: '',
  description: '',
  deadlineLocal: '',
  budget: '',
})

const errors = reactive({
  name: '',
  deadlineLocal: '',
  budget: '',
})

const touched = ref(false)
const submitting = ref(false)
const serverError = ref('')

const canSubmit = computed(() => {
  return (
    form.name.trim().length > 0 &&
    form.deadlineLocal.length > 0 &&
    String(form.budget).trim().length > 0 &&
    !submitting.value
  )
})

function toIsoZFromLocal(localValue) {
  const d = new Date(localValue)
  if (Number.isNaN(d.getTime())) return null
  return d.toISOString()
}

function validate() {
  errors.name = form.name.trim() ? '' : 'Name is required'
  errors.deadlineLocal = form.deadlineLocal ? '' : 'Deadline is required'
  const budgetNum = Number(form.budget)
  errors.budget = Number.isFinite(budgetNum) && budgetNum > 0 ? '' : 'Budget must be a number greater than 0'

  const iso = form.deadlineLocal ? toIsoZFromLocal(form.deadlineLocal) : null
  if (!errors.deadlineLocal && iso) {
    const deadline = new Date(iso)
    if (deadline.getTime() <= Date.now()) {
      errors.deadlineLocal = 'Deadline must be in the future'
    }
  }

  return !errors.name && !errors.deadlineLocal && !errors.budget
}

async function submit() {
  touched.value = true
  serverError.value = ''
  if (!validate()) return

  submitting.value = true
  try {
    const iso = toIsoZFromLocal(form.deadlineLocal)
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() ? form.description.trim() : null,
      deadline: iso,
      budget: Number(form.budget),
    }
    const created = await createActivity(payload)
    await router.push({ name: 'activity-detail', params: { id: created.id } })
  } catch (e) {
    serverError.value = e?.response?.data?.error?.message ?? e.message ?? 'Create failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>New activity</h1>
        <p class="subhead">Creates an activity via <code>POST /api/v1/activities</code> (system admin only).</p>
      </div>
    </header>

    <div class="card">
      <label class="field">
        <span>Name</span>
        <input v-model="form.name" autocomplete="off" />
        <small v-if="touched && errors.name" class="err">{{ errors.name }}</small>
      </label>

      <label class="field">
        <span>Description (optional)</span>
        <textarea v-model="form.description" rows="4"></textarea>
      </label>

      <label class="field">
        <span>Deadline</span>
        <input v-model="form.deadlineLocal" type="datetime-local" />
        <small v-if="touched && errors.deadlineLocal" class="err">{{ errors.deadlineLocal }}</small>
      </label>

      <label class="field">
        <span>Budget</span>
        <input v-model="form.budget" inputmode="decimal" autocomplete="off" />
        <small v-if="touched && errors.budget" class="err">{{ errors.budget }}</small>
      </label>

      <p v-if="serverError" class="err" role="alert">{{ serverError }}</p>

      <div class="actions">
        <button type="button" class="btn secondary" @click="router.back()">Cancel</button>
        <button type="button" class="btn primary" :disabled="!canSubmit" @click="submit">
          {{ submitting ? 'Creating…' : 'Create' }}
        </button>
      </div>
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
.subhead {
  margin: 0;
  color: #4b5563;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0.75rem 0;
}
input,
textarea {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.55rem 0.65rem;
  font: inherit;
  background: #fff;
}
.actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
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
.err {
  color: #b91c1c;
}
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}
</style>
