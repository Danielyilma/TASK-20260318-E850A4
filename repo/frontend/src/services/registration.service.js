import { apiClient } from './api'

export async function createRegistration(payload) {
  const { data } = await apiClient.post('/registrations', payload)
  return data
}

export async function listRegistrations(params = {}) {
  const { data } = await apiClient.get('/registrations', { params })
  return data
}

export async function getRegistration(registrationId) {
  const { data } = await apiClient.get(`/registrations/${registrationId}`)
  return data
}

export async function updateRegistration(registrationId, payload) {
  const { data } = await apiClient.put(`/registrations/${registrationId}`, payload)
  return data
}

export async function deleteRegistration(registrationId) {
  const { data } = await apiClient.delete(`/registrations/${registrationId}`)
  return data
}

export async function submitRegistration(registrationId) {
  const { data } = await apiClient.patch(`/registrations/${registrationId}/submit`)
  return data
}

export async function cancelRegistration(registrationId) {
  const { data } = await apiClient.patch(`/registrations/${registrationId}/cancel`)
  return data
}

export async function listChecklist(registrationId) {
  const { data } = await apiClient.get(`/registrations/${registrationId}/checklist`)
  return data
}

export async function uploadMaterial(registrationId, itemId, file) {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post(
    `/registrations/${registrationId}/materials/${itemId}/upload`,
    body,
    {
      timeout: 120000,
    },
  )
  return data
}

export async function listMaterialVersions(registrationId, itemId) {
  const { data } = await apiClient.get(`/registrations/${registrationId}/materials/${itemId}/versions`)
  return data
}

export async function patchMaterialVersionLabel(registrationId, itemId, versionId, label) {
  const { data } = await apiClient.patch(
    `/registrations/${registrationId}/materials/${itemId}/versions/${versionId}/label`,
    { label },
  )
  return data
}

export async function downloadMaterialBlob(versionId) {
  const { data } = await apiClient.get(`/materials/${versionId}/download`, {
    responseType: 'blob',
    timeout: 120000,
  })
  return data
}
