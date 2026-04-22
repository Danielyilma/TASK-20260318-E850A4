import { apiClient } from './api'

export async function getFundingForRegistration(registrationId) {
  const { data } = await apiClient.get(`/registrations/${registrationId}/funding`)
  return data
}

export async function listFundingAccounts(params = {}) {
  const { data } = await apiClient.get('/funding-accounts', { params })
  return data
}

export async function getFundingAccount(accountId) {
  const { data } = await apiClient.get(`/funding-accounts/${accountId}`)
  return data
}

export async function listTransactions(accountId, params = {}) {
  const { data } = await apiClient.get(`/funding-accounts/${accountId}/transactions`, { params })
  return data
}

export async function createTransaction(accountId, payload) {
  return apiClient.post(`/funding-accounts/${accountId}/transactions`, payload, {
    validateStatus: (status) => (status >= 200 && status < 300) || status === 403,
  })
}

export async function updateTransaction(accountId, transactionId, payload) {
  return apiClient.put(`/funding-accounts/${accountId}/transactions/${transactionId}`, payload, {
    validateStatus: (status) => (status >= 200 && status < 300) || status === 403,
  })
}

export async function deleteTransaction(accountId, transactionId) {
  const { data } = await apiClient.delete(`/funding-accounts/${accountId}/transactions/${transactionId}`)
  return data
}

export async function uploadInvoice(accountId, transactionId, file) {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post(
    `/funding-accounts/${accountId}/transactions/${transactionId}/invoice`,
    body,
    { timeout: 120000 },
  )
  return data
}

export async function getFundingStatistics(params = {}) {
  const { data } = await apiClient.get('/statistics/funding', { params })
  return data
}

export async function getFundingAccountStatistics(accountId) {
  const { data } = await apiClient.get(`/statistics/funding/${accountId}`)
  return data
}
