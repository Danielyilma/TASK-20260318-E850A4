<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { getActivity } from '../services/activity.service'
import * as regApi from '../services/registration.service'
import { validateMaterialFileForUpload, validateTotalUploadBudget } from '../utils/materialFile'

const route = useRoute()
const router = useRouter()

const activityIdFromQuery = computed(() => String(route.query.activity_id ?? ''))
const registrationIdParam = computed(() => String(route.params.registrationId ?? ''))
const isNewFlow = computed(() => route.name === 'registration-new')

const loading = ref(false)
const error = ref('')
const activity = ref(null)
const registration = ref(null)
const checklist = ref({ items: [] })
const versionsByItem = ref({})

const form = ref({
  project_title: '',
  project_description: '',
  target_beneficiaries: 100,
  start_date: '',
  end_date: '',
})
const requestedFunding = ref('5000')

const supplementaryRemainingMs = ref(null)
let tickTimer

function defaultFormDates() {
  const y = new Date().getUTCFullYear()
  form.value.start_date = `${y + 1}-06-01`
  form.value.end_date = `${y + 1}-12-31`
}

function tickSupplementary() {
  const dl = registration.value?.supplementary_deadline
  if (!dl) {
    supplementaryRemainingMs.value = null
    return
  }
  const end = new Date(dl).getTime()
  supplementaryRemainingMs.value = Math.max(0, end - Date.now())
}

function formatDuration(ms) {
  if (ms == null) return ''
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${h}h ${m}m ${sec}s`
}

async function loadChecklistAndVersions() {
  const rid = registration.value?.id
  if (!rid) return
  const cl = await regApi.listChecklist(rid)
  checklist.value = cl
  const map = {}
  for (const item of cl.items ?? []) {
    const v = await regApi.listMaterialVersions(rid, item.id)
    map[item.id] = v
  }
  versionsByItem.value = map
}

const totalUploadedBytes = computed(() => {
  let sum = 0
  for (const vlist of Object.values(versionsByItem.value)) {
    for (const v of vlist?.versions ?? []) {
      sum += v.file_size_bytes ?? 0
    }
  }
  return sum
})

const canEditMaterials = computed(
  () =>
    Boolean(registration.value) &&
    ['draft', 'needs_correction', 'supplemented'].includes(registration.value.status) &&
    !registration.value.is_locked,
)

async function loadRegistrationBundle() {
  loading.value = true
  error.value = ''
  try {
    const rid = registrationIdParam.value
    registration.value = await regApi.getRegistration(rid)
    if (registration.value.status === 'draft' && registration.value.form_data) {
      Object.assign(form.value, registration.value.form_data)
      requestedFunding.value = String(registration.value.requested_funding)
    }
    activity.value = await getActivity(registration.value.activity_id)
    await loadChecklistAndVersions()
  } catch (e) {
    registration.value = null
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load registration'
  } finally {
    loading.value = false
  }
}

async function loadActivityOnly() {
  loading.value = true
  error.value = ''
  try {
    const aid = activityIdFromQuery.value
    if (!aid) {
      error.value = 'Missing activity_id query parameter.'
      return
    }
    activity.value = await getActivity(aid)
    defaultFormDates()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load activity'
  } finally {
    loading.value = false
  }
}

async function createDraft() {
  loading.value = true
  error.value = ''
  try {
    const payload = {
      activity_id: activityIdFromQuery.value,
      form_data: { ...form.value, target_beneficiaries: Number(form.value.target_beneficiaries) },
      requested_funding: Number(requestedFunding.value),
    }
    const created = await regApi.createRegistration(payload)
    await router.replace({ name: 'registration-wizard', params: { registrationId: created.id } })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Create failed'
  } finally {
    loading.value = false
  }
}

async function saveDraft() {
  if (!registration.value || registration.value.status !== 'draft') return
  loading.value = true
  error.value = ''
  try {
    const payload = {
      form_data: { ...form.value, target_beneficiaries: Number(form.value.target_beneficiaries) },
      requested_funding: Number(requestedFunding.value),
    }
    registration.value = await regApi.updateRegistration(registration.value.id, payload)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Save failed'
  } finally {
    loading.value = false
  }
}

const uploadErrors = ref({})

async function onPickFile(item, event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  uploadErrors.value[item.id] = ''
  if (!file || !registration.value) return

  const allowed = (item.allowed_types ?? []).map((t) => String(t).toLowerCase())
  const v1 = validateMaterialFileForUpload(file, allowed)
  if (!v1.ok) {
    uploadErrors.value[item.id] = v1.error
    return
  }
  const v2 = validateTotalUploadBudget(totalUploadedBytes.value, file)
  if (!v2.ok) {
    uploadErrors.value[item.id] = v2.error
    return
  }

  loading.value = true
  error.value = ''
  try {
    await regApi.uploadMaterial(registration.value.id, item.id, file)
    await loadChecklistAndVersions()
  } catch (e) {
    uploadErrors.value[item.id] = e?.response?.data?.error?.message ?? e.message ?? 'Upload failed'
  } finally {
    loading.value = false
  }
}

async function setLabel(itemId, versionId, label) {
  if (!registration.value) return
  loading.value = true
  error.value = ''
  try {
    await regApi.patchMaterialVersionLabel(registration.value.id, itemId, versionId, label)
    await loadChecklistAndVersions()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Label update failed'
  } finally {
    loading.value = false
  }
}

async function downloadVersion(versionId) {
  try {
    const blob = await regApi.downloadMaterialBlob(versionId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'material'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Download failed'
  }
}

async function submitApp() {
  if (!registration.value) return
  loading.value = true
  error.value = ''
  try {
    await regApi.submitRegistration(registration.value.id)
    await loadRegistrationBundle()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Submit failed'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  tickTimer = setInterval(tickSupplementary, 1000)
  if (isNewFlow.value) {
    await loadActivityOnly()
  } else if (registrationIdParam.value) {
    await loadRegistrationBundle()
  }
})

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
})

watch(
  () => registration.value?.supplementary_deadline,
  () => tickSupplementary(),
)

watch(registrationIdParam, async (id, prev) => {
  if (!isNewFlow.value && id && id !== prev) {
    await loadRegistrationBundle()
  }
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>{{ isNewFlow ? 'New registration' : 'Registration' }}</h1>
        <p v-if="activity" class="subhead">{{ activity.name }}</p>
      </div>
      <RouterLink class="btn secondary" to="/activities">Back to activities</RouterLink>
    </header>
    <nav v-if="!isNewFlow && registration" class="wiz-nav" aria-label="Registration sections">
      <a href="#application-form">Application form</a>
      <a href="#materials">Materials</a>
      <a href="#submit">Submit</a>
    </nav>

    <p v-if="error" class="err" role="alert">{{ error }}</p>
    <p v-if="loading" class="muted">Loading…</p>

    <div v-if="isNewFlow && activity && !loading" class="card">
      <h2>Step 1 — Application details</h2>
      <div class="grid-form">
        <label>Project title<input v-model="form.project_title" class="inp" type="text" /></label>
        <label class="full"
          >Description <textarea v-model="form.project_description" class="inp" rows="3"></textarea
        ></label>
        <label>Target beneficiaries<input v-model.number="form.target_beneficiaries" class="inp" type="number" min="1" /></label>
        <label>Start date<input v-model="form.start_date" class="inp" type="date" /></label>
        <label>End date<input v-model="form.end_date" class="inp" type="date" /></label>
        <label>Requested funding<input v-model="requestedFunding" class="inp" type="number" min="0" step="0.01" /></label>
      </div>
      <button type="button" class="btn primary" :disabled="loading" @click="createDraft">Create draft &amp; continue</button>
    </div>

    <div v-if="!isNewFlow && registration" class="stack">
      <div class="card row-between">
        <div>
          <div class="pill" :data-status="registration.status">{{ registration.status }}</div>
          <p class="muted small">Deadline {{ registration.deadline }}</p>
        </div>
        <button v-if="registration.status === 'draft'" type="button" class="btn secondary" :disabled="loading" @click="saveDraft">
          Save draft
        </button>
      </div>

      <div v-if="registration.supplementary_deadline" class="card countdown">
        <h3>Supplementary window</h3>
        <p v-if="supplementaryRemainingMs === 0" class="err">Window closed — uploads may be blocked by the server.</p>
        <p v-else class="mono">Time remaining: {{ formatDuration(supplementaryRemainingMs) }}</p>
      </div>

      <div id="application-form" v-if="registration.status === 'draft'" class="card">
        <h2>Application form</h2>
        <fieldset class="grid-form" :disabled="registration.is_locked">
          <label>Project title<input v-model="form.project_title" class="inp" type="text" /></label>
          <label class="full"
            >Description <textarea v-model="form.project_description" class="inp" rows="3"></textarea
          ></label>
          <label>Target beneficiaries<input v-model.number="form.target_beneficiaries" class="inp" type="number" min="1" /></label>
          <label>Start date<input v-model="form.start_date" class="inp" type="date" /></label>
          <label>End date<input v-model="form.end_date" class="inp" type="date" /></label>
          <label>Requested funding<input v-model="requestedFunding" class="inp" type="number" min="0" step="0.01" /></label>
        </fieldset>
        <p v-if="registration.is_locked" class="muted small">This registration is locked; edits are disabled.</p>
      </div>

      <div id="materials" class="card">
        <h2>Materials</h2>
        <p class="muted small">Total uploaded (this registration): {{ (totalUploadedBytes / (1024 * 1024)).toFixed(2) }} MB / 200 MB</p>
        <p v-if="!canEditMaterials" class="muted small">Materials are locked due to registration state or deadline.</p>
        <p v-if="!(checklist.items?.length)" class="muted">No checklist items yet. A system administrator must add required documents.</p>
        <div v-for="item in checklist.items ?? []" :key="item.id" class="mat-row">
          <div>
            <strong>{{ item.item_name }}</strong>
            <span v-if="item.is_required" class="req">required</span>
            <p class="muted small">Allowed: {{ (item.allowed_types ?? []).join(', ') }} · per file ≤ {{ item.max_file_size_mb }}MB</p>
            <p v-if="uploadErrors[item.id]" class="err small">{{ uploadErrors[item.id] }}</p>
            <input
              v-if="['draft', 'needs_correction', 'supplemented'].includes(registration.status)"
              type="file"
              class="file"
              :disabled="!canEditMaterials"
              :aria-disabled="!canEditMaterials"
              @change="onPickFile(item, $event)"
            />
          </div>
          <div class="versions">
            <div v-for="v in versionsByItem[item.id]?.versions ?? []" :key="v.id" class="ver">
              <span class="mono">{{ v.file_name }}</span>
              <span class="muted small">v{{ v.version_number }} · {{ v.label }}</span>
              <div class="row-actions">
                <button type="button" class="btn tiny" @click="downloadVersion(v.id)">Download</button>
                <select
                  v-if="['draft', 'needs_correction', 'supplemented'].includes(registration.status)"
                  class="sel"
                  :value="v.label"
                  :disabled="!canEditMaterials"
                  @change="setLabel(item.id, v.id, $event.target.value)"
                >
                  <option value="pending_submission">pending_submission</option>
                  <option value="submitted">submitted</option>
                  <option value="needs_correction">needs_correction</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="submit" v-if="registration.status === 'draft'" class="card">
        <h2>Submit</h2>
        <p class="muted small">Required materials must have at least one version labeled <code>submitted</code>.</p>
        <button type="button" class="btn primary" :disabled="loading || registration.is_locked" @click="submitApp">
          Submit registration
        </button>
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
h1 {
  margin: 0 0 0.35rem;
}
h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}
.subhead {
  margin: 0;
  color: #6b7280;
}
.wiz-nav {
  display: flex;
  gap: 1rem;
  margin: 0 0 1rem;
}
.wiz-nav a {
  font-weight: 700;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
  margin-bottom: 1rem;
}
.stack {
  display: flex;
  flex-direction: column;
}
.grid-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem 1rem;
  margin-bottom: 1rem;
}
.grid-form label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
}
.full {
  grid-column: 1 / -1;
}
.inp {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.45rem 0.55rem;
  font: inherit;
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
.btn.secondary {
  background: #f3f4f6;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn.tiny {
  padding: 0.25rem 0.45rem;
  font-size: 0.8rem;
}
.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}
.pill {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  background: #e5e7eb;
}
.countdown {
  border-color: #fcd34d;
  background: #fffbeb;
}
.mat-row {
  border-top: 1px solid #e5e7eb;
  padding: 0.85rem 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.req {
  margin-left: 0.35rem;
  font-size: 0.75rem;
  color: #b45309;
  font-weight: 700;
}
.versions {
  font-size: 0.9rem;
}
.ver {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: #fff;
}
.row-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 0.35rem;
}
.sel {
  font: inherit;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  padding: 0.2rem 0.35rem;
}
.file {
  margin-top: 0.35rem;
}
.muted {
  color: #6b7280;
}
.small {
  font-size: 0.85rem;
}
.err {
  color: #b91c1c;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
