<script setup>
import { computed, onMounted, ref } from 'vue'
import * as regApi from '../services/registration.service'
import * as reviewApi from '../services/review.service'

const loading = ref(false)
const error = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = ref(20)
const statusFilter = ref('')

const selected = ref(new Set())

const modalOpen = ref(false)
const modalAction = ref('approve')
const modalComment = ref('')
const modalCorrectionReason = ref('')
const verifyOpen = ref(false)
const verifyPayload = ref(null)

const selectedIds = computed(() => Array.from(selected.value))

function toggle(id) {
  const s = new Set(selected.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selected.value = s
}

function toggleAllOnPage() {
  const ids = (items.value ?? []).map((r) => r.id)
  const s = new Set(selected.value)
  const allOn = ids.every((id) => s.has(id))
  if (allOn) {
    ids.forEach((id) => s.delete(id))
  } else {
    ids.forEach((id) => s.add(id))
  }
  selected.value = s
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = { page: page.value, per_page: perPage.value }
    if (statusFilter.value) params.status = statusFilter.value
    const data = await regApi.listRegistrations(params)
    items.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load'
  } finally {
    loading.value = false
  }
}

function openReviewModal() {
  modalOpen.value = true
}

function selectSingle(id) {
  selected.value = new Set([id])
  openReviewModal()
}

async function applyBatchFromModal() {
  if (!selectedIds.value.length) {
    error.value = 'Select at least one registration.'
    return
  }
  if (modalAction.value === 'request_correction' && !modalCorrectionReason.value.trim()) {
    error.value = 'correction_reason is required for request_correction.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const body = {
      registration_ids: selectedIds.value,
      action: modalAction.value,
      comment: modalComment.value || null,
    }
    if (modalAction.value === 'request_correction') {
      body.correction_reason = modalCorrectionReason.value
    }
    await reviewApi.batchReview(body)
    modalOpen.value = false
    selected.value = new Set()
    modalComment.value = ''
    modalCorrectionReason.value = ''
    await load()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Batch failed'
  } finally {
    loading.value = false
  }
}

async function openVerify(registrationId) {
  verifyOpen.value = true
  verifyPayload.value = null
  loading.value = true
  error.value = ''
  try {
    verifyPayload.value = await reviewApi.verifySensitive(registrationId)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Verify failed'
    verifyOpen.value = false
  } finally {
    loading.value = false
  }
}


onMounted(load)
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Review dashboard</h1>
        <p class="muted">Live data from <code>/registrations</code> and review endpoints.</p>
      </div>
      <button type="button" class="btn" :disabled="loading" @click="load">Refresh</button>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div class="toolbar card">
      <label
        >Status
        <select v-model="statusFilter" class="inp" @change=";(page = 1), load()">
          <option value="">(all)</option>
          <option value="draft">draft</option>
          <option value="submitted">submitted</option>
          <option value="supplemented">supplemented</option>
          <option value="needs_correction">needs_correction</option>
          <option value="waitlisted">waitlisted</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </label>
      <button type="button" class="btn primary" :disabled="!selectedIds.length" @click="openReviewModal">
        Review selected ({{ selectedIds.length }})
      </button>
    </div>

    <div class="card">
      <table class="tbl">
        <thead>
          <tr>
            <th><input type="checkbox" aria-label="Select page" @change="toggleAllOnPage" /></th>
            <th>ID</th>
            <th>Status</th>
            <th>Funding</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="row.id">
            <td><input type="checkbox" :checked="selected.has(row.id)" @change="toggle(row.id)" /></td>
            <td class="mono">{{ row.id }}</td>
            <td>{{ row.status }}</td>
            <td class="num">{{ row.requested_funding }}</td>
            <td class="mono small">{{ row.created_at }}</td>
            <td>
              <button type="button" class="linkish" @click="selectSingle(row.id)">Review</button>
              ·
              <button type="button" class="linkish" @click="openVerify(row.id)">Verify sensitive</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="muted small">Total {{ total }} — page {{ page }}</p>
    </div>

    <div v-if="modalOpen" class="backdrop" @click.self="modalOpen = false">
      <div class="modal card">
        <h2>Review action</h2>
        <label
          >Action
          <select v-model="modalAction" class="inp">
            <option value="approve">approve</option>
            <option value="reject">reject</option>
            <option value="request_correction">request_correction</option>
            <option value="waitlist">waitlist</option>
            <option value="cancel">cancel</option>
          </select>
        </label>
        <label>Comment <textarea v-model="modalComment" class="inp" rows="2"></textarea></label>
        <label v-if="modalAction === 'request_correction'"
          >Correction reason <textarea v-model="modalCorrectionReason" class="inp" rows="2"></textarea
        ></label>
        <div class="row">
          <button type="button" class="btn" @click="modalOpen = false">Close</button>
          <button type="button" class="btn primary" :disabled="loading" @click="applyBatchFromModal">Apply</button>
        </div>
      </div>
    </div>

    <div v-if="verifyOpen" class="backdrop" @click.self="verifyOpen = false">
      <div class="modal card">
        <h2>Sensitive verification</h2>
        <p v-if="!verifyPayload" class="muted">Loading…</p>
        <template v-else>
          <p><strong>Applicant</strong> {{ verifyPayload.applicant_id }}</p>
          <p><strong>ID number</strong> {{ verifyPayload.id_number }}</p>
          <p><strong>Contact</strong> {{ verifyPayload.contact_info }}</p>
          <p class="muted small mono">Audit {{ verifyPayload.audit_log_id }} at {{ verifyPayload.verified_at }}</p>
        </template>
        <button type="button" class="btn" @click="verifyOpen = false">Close</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}
h1 {
  margin: 0 0 0.35rem;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  background: #fafafa;
  margin-bottom: 1rem;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}
.inp {
  display: block;
  margin-top: 0.25rem;
  width: 100%;
  min-width: 12rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.4rem 0.5rem;
  font: inherit;
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.tbl th,
.tbl td {
  border-bottom: 1px solid #e5e7eb;
  padding: 0.45rem 0.35rem;
  text-align: left;
  vertical-align: top;
}
.btn {
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.5rem 0.8rem;
  font-weight: 700;
  cursor: pointer;
}
.btn.primary {
  background: #2563eb;
  border-color: #1d4ed8;
  color: #fff;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 50;
}
.modal {
  max-width: 420px;
  width: 100%;
  background: #fff;
}
.modal h2 {
  margin-top: 0;
}
.modal label {
  display: block;
  margin: 0.65rem 0;
  font-weight: 600;
  font-size: 0.9rem;
}
.row {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
.linkish {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.muted {
  color: #6b7280;
}
.small {
  font-size: 0.82rem;
}
.mono {
  font-family: ui-monospace, monospace;
  word-break: break-all;
}
.num {
  font-variant-numeric: tabular-nums;
}
.err {
  color: #b91c1c;
}
</style>
