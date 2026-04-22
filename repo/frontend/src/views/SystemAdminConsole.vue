<script setup>
import { onMounted, ref } from 'vue'
import * as phase5 from '../services/phase5.service'
import LoadingButton from '../components/LoadingButton.vue'

const tab = ref('alerts')
const loading = ref(false)
const error = ref('')

const alerts = ref({ items: [], total: 0 })
const audit = ref({ items: [], total: 0 })
const batches = ref({ items: [], total: 0 })
const reports = ref({ items: [], total: 0 })
const backups = ref({ items: [], total: 0 })

const batchName = ref('Validation batch')
const batchJson = ref(
  JSON.stringify(
    {
      activity_ids: [],
      statuses: ['submitted', 'draft'],
      validation_types: ['type_check', 'mandatory_check'],
    },
    null,
    2,
  ),
)

const reportStart = ref('')
const reportEnd = ref('')

async function loadAlerts() {
  loading.value = true
  error.value = ''
  try {
    alerts.value = await phase5.listAlerts({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function loadAudit() {
  loading.value = true
  error.value = ''
  try {
    audit.value = await phase5.listAuditLogs({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function loadBatches() {
  loading.value = true
  error.value = ''
  try {
    batches.value = await phase5.listDataCollectionBatches({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function loadReports() {
  loading.value = true
  error.value = ''
  try {
    reports.value = await phase5.listReports({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function loadBackups() {
  loading.value = true
  error.value = ''
  try {
    backups.value = await phase5.listBackups({ page: 1, per_page: 50 })
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function ack(id) {
  loading.value = true
  error.value = ''
  try {
    await phase5.acknowledgeAlert(id)
    await loadAlerts()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed'
  } finally {
    loading.value = false
  }
}

async function createBatch() {
  loading.value = true
  error.value = ''
  try {
    const scope = JSON.parse(batchJson.value)
    await phase5.createDataCollectionBatch({ name: batchName.value, scope_whitelist: scope })
    await loadBatches()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Invalid JSON or request failed'
  } finally {
    loading.value = false
  }
}

async function execBatch(id) {
  loading.value = true
  error.value = ''
  try {
    await phase5.executeDataCollectionBatch(id)
    await loadBatches()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Execute failed'
  } finally {
    loading.value = false
  }
}

async function genAuditCsv() {
  loading.value = true
  error.value = ''
  try {
    const body = { format: 'csv' }
    if (reportStart.value) body.start_date = reportStart.value
    if (reportEnd.value) body.end_date = reportEnd.value
    const rep = await phase5.postAuditReport(body)
    const blob = await phase5.downloadReport(rep.report_id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = rep.file_name || 'report.csv'
    a.click()
    URL.revokeObjectURL(url)
    await loadReports()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Report failed'
  } finally {
    loading.value = false
  }
}

async function triggerBackup() {
  loading.value = true
  error.value = ''
  try {
    await phase5.createBackup()
    await loadBackups()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Backup failed'
  } finally {
    loading.value = false
  }
}

async function restore(id) {
  loading.value = true
  error.value = ''
  try {
    await phase5.restoreBackup(id)
    await loadBackups()
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Restore failed'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAlerts()
  loadAudit()
  loadBatches()
  loadReports()
  loadBackups()
})
</script>

<template>
  <section class="page">
    <header class="hdr">
      <h1>System admin</h1>
      <p class="muted">Alerts, audit trail, data batches, and reports (live API).</p>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <nav class="tabs">
      <button type="button" :class="{ on: tab === 'alerts' }" @click="tab = 'alerts'">Alerts</button>
      <button type="button" :class="{ on: tab === 'audit' }" @click="tab = 'audit'">Audit logs</button>
      <button type="button" :class="{ on: tab === 'batches' }" @click="tab = 'batches'">Data batches</button>
      <button type="button" :class="{ on: tab === 'reports' }" @click="tab = 'reports'">Reports</button>
      <button type="button" :class="{ on: tab === 'backups' }" @click="tab = 'backups'">Backups</button>
    </nav>

    <div v-show="tab === 'alerts'" class="card">
      <div class="row">
        <LoadingButton :loading="loading" variant="primary" @click="loadAlerts">Refresh</LoadingButton>
      </div>
      <table class="tbl">
        <thead>
          <tr>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Ack</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in alerts.items" :key="a.id">
            <td>{{ a.alert_type }}</td>
            <td>{{ a.severity }}</td>
            <td>{{ a.message }}</td>
            <td>
              <button v-if="!a.acknowledged" type="button" class="link" @click="ack(a.id)">Acknowledge</button>
              <span v-else class="muted">done</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="tab === 'audit'" class="card">
      <LoadingButton :loading="loading" variant="primary" @click="loadAudit">Refresh</LoadingButton>
      <table class="tbl">
        <thead>
          <tr>
            <th>When</th>
            <th>User</th>
            <th>Action</th>
            <th>Resource</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="x in audit.items" :key="x.id">
            <td class="mono small">{{ x.created_at }}</td>
            <td>{{ x.username || x.user_id || '—' }}</td>
            <td>{{ x.action }}</td>
            <td class="mono small">{{ x.resource_type }} {{ x.resource_id }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="tab === 'batches'" class="card">
      <h2>Create batch</h2>
      <label class="blk">Name <input v-model="batchName" class="inp" type="text" /></label>
      <label class="blk">Scope JSON <textarea v-model="batchJson" class="inp ta" rows="8"></textarea></label>
      <LoadingButton :loading="loading" variant="primary" @click="createBatch">Create</LoadingButton>

      <h2 class="mt">Existing batches</h2>
      <LoadingButton :loading="loading" class="mb" @click="loadBatches">Refresh</LoadingButton>
      <table class="tbl">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Execute</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in batches.items" :key="b.id">
            <td>{{ b.name }}</td>
            <td>{{ b.status }}</td>
            <td>
              <button
                v-if="b.status === 'pending'"
                type="button"
                class="link"
                @click="execBatch(b.id)"
              >
                Run
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="tab === 'reports'" class="card">
      <h2>Generate audit CSV</h2>
      <label class="blk">Start (ISO, optional) <input v-model="reportStart" class="inp" type="text" /></label>
      <label class="blk">End (ISO, optional) <input v-model="reportEnd" class="inp" type="text" /></label>
      <LoadingButton :loading="loading" variant="primary" @click="genAuditCsv">Download CSV</LoadingButton>

      <h2 class="mt">Recent reports</h2>
      <LoadingButton :loading="loading" class="mb" @click="loadReports">Refresh</LoadingButton>
      <ul class="rep">
        <li v-for="r in reports.items" :key="r.report_id">
          {{ r.report_type }} · {{ r.file_name }} · {{ r.format }}
        </li>
      </ul>
    </div>

    <div v-show="tab === 'backups'" class="card">
      <h2>Local backups</h2>
      <p class="muted small">
        Manual backups include database dump and local upload archive. Restore temporarily locks the platform.
      </p>
      <div class="row">
        <LoadingButton :loading="loading" variant="primary" @click="triggerBackup">Create backup</LoadingButton>
        <LoadingButton :loading="loading" @click="loadBackups">Refresh</LoadingButton>
      </div>
      <table class="tbl">
        <thead>
          <tr>
            <th>Created</th>
            <th>Status</th>
            <th>Type</th>
            <th>Size</th>
            <th>Restore</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in backups.items" :key="b.id">
            <td class="mono small">{{ b.created_at }}</td>
            <td>{{ b.status }}</td>
            <td>{{ b.backup_type }}</td>
            <td>{{ b.size_bytes }}</td>
            <td>
              <button
                v-if="b.status === 'completed'"
                type="button"
                class="link"
                :disabled="loading"
                @click="restore(b.id)"
              >
                Restore
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page {
  max-width: 960px;
}
.hdr h1 {
  margin: 0 0 0.35rem;
}
.muted {
  color: #6b7280;
}
.err {
  color: #b91c1c;
}
.tabs {
  display: flex;
  gap: 0.35rem;
  margin: 1rem 0;
}
.tabs button {
  border: 1px solid #d1d5db;
  background: #f9fafb;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}
.tabs button.on {
  background: #2563eb;
  color: #fff;
  border-color: #1d4ed8;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  background: #fafafa;
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;
  font-size: 0.88rem;
}
.tbl th,
.tbl td {
  border-bottom: 1px solid #e5e7eb;
  padding: 0.4rem;
  text-align: left;
  vertical-align: top;
}
.link {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 700;
  cursor: pointer;
}
.blk {
  display: block;
  margin: 0.5rem 0;
  font-weight: 600;
  font-size: 0.9rem;
}
.inp {
  display: block;
  margin-top: 0.25rem;
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.45rem;
  font: inherit;
}
.ta {
  font-family: ui-monospace, monospace;
}
.mt {
  margin-top: 1.25rem;
}
.mb {
  margin-bottom: 0.5rem;
}
.row {
  margin-bottom: 0.5rem;
}
.mono {
  font-family: ui-monospace, monospace;
}
.small {
  font-size: 0.8rem;
}
.rep {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
}
</style>
