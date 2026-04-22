import { apiClient } from './api'

export async function listAlerts(params = {}) {
  const { data } = await apiClient.get('/alerts', { params })
  return data
}

export async function acknowledgeAlert(alertId) {
  const { data } = await apiClient.patch(`/alerts/${alertId}/acknowledge`)
  return data
}

export async function listAuditLogs(params = {}) {
  const { data } = await apiClient.get('/audit-logs', { params })
  return data
}

export async function listDataCollectionBatches(params = {}) {
  const { data } = await apiClient.get('/data-collection/batches', { params })
  return data
}

export async function createDataCollectionBatch(payload) {
  const { data } = await apiClient.post('/data-collection/batches', payload)
  return data
}

export async function executeDataCollectionBatch(batchId) {
  const { data } = await apiClient.patch(`/data-collection/batches/${batchId}/execute`)
  return data
}

export async function listReports(params = {}) {
  const { data } = await apiClient.get('/reports', { params })
  return data
}

export async function postAuditReport(payload) {
  const { data } = await apiClient.post('/reports/audit', payload)
  return data
}

export async function postReconciliationReport(payload) {
  const { data } = await apiClient.post('/reports/reconciliation', payload)
  return data
}

export async function postComplianceReport(payload) {
  const { data } = await apiClient.post('/reports/compliance', payload)
  return data
}

export async function downloadReport(reportId) {
  const { data } = await apiClient.get(`/reports/${reportId}/download`, {
    responseType: 'blob',
    timeout: 120000,
  })
  return data
}

export async function listBackups(params = {}) {
  const { data } = await apiClient.get('/backups', { params })
  return data
}

export async function createBackup() {
  const { data } = await apiClient.post('/backups')
  return data
}

export async function restoreBackup(backupId) {
  const { data } = await apiClient.post(`/backups/${backupId}/restore`)
  return data
}
