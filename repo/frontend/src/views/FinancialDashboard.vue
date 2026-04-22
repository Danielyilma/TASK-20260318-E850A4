<script setup>
import { computed, onMounted, ref } from 'vue'
import * as fundingApi from '../services/funding.service'
import { MAX_MATERIAL_FILE_BYTES } from '../utils/materialFile'

const loading = ref(false)
const error = ref('')
const accounts = ref([])
const total = ref(0)

const selectedAccountId = ref('')
const accountDetail = ref(null)
const transactions = ref([])

const txForm = ref({
  type: 'expense',
  amount: '',
  category: '',
  description: '',
})

const overspendModal = ref(false)
const overspendDetail = ref(null)
const pendingTxPayload = ref(null)

const invoiceFile = ref(null)
const overallStats = ref(null)
const accountStats = ref(null)

const maxInvoiceBytes = MAX_MATERIAL_FILE_BYTES

async function loadAccounts() {
  loading.value = true
  error.value = ''
  try {
    const data = await fundingApi.listFundingAccounts({ page: 1, per_page: 100 })
    overallStats.value = await fundingApi.getFundingStatistics({ group_by: 'category' })
    accounts.value = data.items ?? []
    total.value = data.total ?? 0
    if (!selectedAccountId.value && accounts.value.length) {
      await selectAccount(accounts.value[0].id)
    }
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load accounts'
  } finally {
    loading.value = false
  }
}

async function selectAccount(id) {
  selectedAccountId.value = id
  loading.value = true
  error.value = ''
  try {
    accountDetail.value = await fundingApi.getFundingAccount(id)
    const tx = await fundingApi.listTransactions(id, { page: 1, per_page: 100 })
    transactions.value = tx.items ?? []
    accountStats.value = await fundingApi.getFundingAccountStatistics(id)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Failed to load account'
  } finally {
    loading.value = false
  }
}

function parseOverspend(errResponse) {
  const d = errResponse?.data
  if (!d) return null
  if (d.error?.code !== 'OVERSPEND_CONFIRMATION_REQUIRED') return null
  return d
}

async function submitTransaction(overrideConfirmed) {
  if (!selectedAccountId.value) return
  const payload = {
    type: txForm.value.type,
    amount: Number(txForm.value.amount),
    category: txForm.value.category,
    description: txForm.value.description || null,
  }
  if (overrideConfirmed) payload.override_confirmed = true

  loading.value = true
  error.value = ''
  overspendModal.value = false
  try {
    const resp = await fundingApi.createTransaction(selectedAccountId.value, payload)
    if (resp.status === 403) {
      const detail = parseOverspend(resp)
      if (detail) {
        pendingTxPayload.value = { ...payload }
        overspendDetail.value = detail
        overspendModal.value = true
        return
      }
    }
    if (resp.status !== 201) {
      error.value = resp.data?.error?.message ?? `Unexpected status ${resp.status}`
      return
    }
    txForm.value = { type: 'expense', amount: '', category: '', description: '' }
    await selectAccount(selectedAccountId.value)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Transaction failed'
  } finally {
    loading.value = false
  }
}

async function confirmOverspend() {
  if (!pendingTxPayload.value) {
    overspendModal.value = false
    return
  }
  const merged = { ...pendingTxPayload.value, override_confirmed: true }
  loading.value = true
  error.value = ''
  overspendModal.value = false
  try {
    const resp = await fundingApi.createTransaction(selectedAccountId.value, merged)
    if (resp.status !== 201) {
      error.value = resp.data?.error?.message ?? `Unexpected status ${resp.status}`
      return
    }
    pendingTxPayload.value = null
    overspendDetail.value = null
    txForm.value = { type: 'expense', amount: '', category: '', description: '' }
    await selectAccount(selectedAccountId.value)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Transaction failed'
  } finally {
    loading.value = false
  }
}

async function uploadInvoiceFor(txId) {
  const f = invoiceFile.value
  if (!f || !selectedAccountId.value) {
    error.value = 'Choose an invoice file first.'
    return
  }
  if (f.size > maxInvoiceBytes) {
    error.value = 'Invoice exceeds 20MB.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await fundingApi.uploadInvoice(selectedAccountId.value, txId, f)
    invoiceFile.value = null
    await selectAccount(selectedAccountId.value)
  } catch (e) {
    error.value = e?.response?.data?.error?.message ?? e.message ?? 'Invoice upload failed'
  } finally {
    loading.value = false
  }
}

const balanceLabel = computed(() => {
  const a = accountDetail.value
  if (!a) return ''
  return `${a.balance} (expenses ${a.total_expenses} / budget ${a.approved_budget})`
})

onMounted(loadAccounts)
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Funding</h1>
        <p class="muted">Accounts and transactions from the live API.</p>
      </div>
      <button type="button" class="btn" :disabled="loading" @click="loadAccounts">Refresh</button>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div class="layout">
      <aside class="card aside">
        <h2>Accounts ({{ total }})</h2>
        <ul class="list">
          <li v-for="a in accounts" :key="a.id">
            <button
              type="button"
              class="acct"
              :class="{ active: a.id === selectedAccountId }"
              @click="selectAccount(a.id)"
            >
              <span class="mono">{{ a.id.slice(0, 8) }}…</span>
              <span class="muted small">budget {{ a.approved_budget }}</span>
            </button>
          </li>
        </ul>
      </aside>

      <div class="main">
        <div v-if="accountDetail" class="card">
          <h2>Account</h2>
          <p class="mono">{{ accountDetail.id }}</p>
          <p>{{ balanceLabel }}</p>
          <p v-if="accountDetail.is_overspent" class="warn">Overspent vs approved budget</p>
        </div>

        <div v-if="overallStats" class="card">
          <h2>Statistics</h2>
          <p class="muted">
            Total accounts {{ overallStats.summary?.total_accounts ?? 0 }},
            overspending rate {{ overallStats.summary?.overspending_rate ?? 0 }}%
          </p>
          <ul class="list">
            <li v-for="row in overallStats.by_category ?? []" :key="row.category" class="small">
              {{ row.category }}: expenses {{ row.total_expenses }} ({{ row.transaction_count }} tx)
            </li>
          </ul>
          <ul v-if="accountStats?.by_category?.length" class="list">
            <li v-for="row in accountStats.by_category" :key="`acct-${row.category}`" class="small">
              This account / {{ row.category }}: {{ row.total_expenses }}
            </li>
          </ul>
        </div>

        <div v-if="accountDetail" class="card">
          <h2>New transaction</h2>
          <div class="grid">
            <label
              >Type
              <select v-model="txForm.type" class="inp">
                <option value="expense">expense</option>
                <option value="income">income</option>
              </select>
            </label>
            <label>Amount <input v-model="txForm.amount" class="inp" type="number" min="0" step="0.01" /></label>
            <label>Category <input v-model="txForm.category" class="inp" type="text" /></label>
            <label class="full"
              >Description <input v-model="txForm.description" class="inp" type="text"
            /></label>
          </div>
          <button type="button" class="btn primary" :disabled="loading" @click="submitTransaction(false)">Record</button>
        </div>

        <div v-if="accountDetail" class="card">
          <h2>Transactions</h2>
          <table class="tbl">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Category</th>
                <th>Invoice</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in transactions" :key="t.id">
                <td class="mono small">{{ t.id.slice(0, 8) }}…</td>
                <td>{{ t.type }}</td>
                <td>{{ t.amount }}</td>
                <td>{{ t.category }}</td>
                <td>
                  <input type="file" accept=".pdf,.png,.jpg,.jpeg" @input="invoiceFile = $event.target.files[0]" />
                  <button type="button" class="btn tiny" :disabled="loading" @click="uploadInvoiceFor(t.id)">Upload</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="overspendModal" class="backdrop" @click.self="overspendModal = false">
      <div class="modal card">
        <h2>Budget threshold</h2>
        <p>{{ overspendDetail?.error?.message }}</p>
        <p v-if="overspendDetail?.overspend_percentage != null" class="muted">
          Projected overspend: {{ overspendDetail.overspend_percentage }}% over budget (threshold
          {{ overspendDetail.threshold }}%).
        </p>
        <div class="row">
          <button type="button" class="btn" @click="overspendModal = false">Cancel</button>
          <button type="button" class="btn primary" :disabled="loading" @click="confirmOverspend">Confirm override</button>
        </div>
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
h2 {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
}
.layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 1rem;
  align-items: start;
}
.aside {
  position: sticky;
  top: 1rem;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.acct {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.45rem 0.5rem;
  margin-bottom: 0.35rem;
  background: #fff;
  cursor: pointer;
}
.acct.active {
  border-color: #2563eb;
  background: #eff6ff;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  background: #fafafa;
  margin-bottom: 1rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}
.grid label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  font-weight: 600;
}
.full {
  grid-column: 1 / -1;
}
.inp {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.4rem 0.5rem;
  font: inherit;
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
.tbl th,
.tbl td {
  border-bottom: 1px solid #e5e7eb;
  padding: 0.4rem;
  text-align: left;
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
.btn.tiny {
  padding: 0.2rem 0.45rem;
  font-size: 0.78rem;
  margin-top: 0.25rem;
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
  max-width: 440px;
  width: 100%;
  background: #fff;
}
.row {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
.muted {
  color: #6b7280;
}
.small {
  font-size: 0.8rem;
}
.mono {
  font-family: ui-monospace, monospace;
}
.err {
  color: #b91c1c;
}
.warn {
  color: #b45309;
  font-weight: 700;
}
@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .aside {
    position: static;
  }
}
</style>
