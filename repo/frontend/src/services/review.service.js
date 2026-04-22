import { apiClient } from './api'

export async function reviewRegistration(registrationId, payload) {
  const { data } = await apiClient.patch(`/registrations/${registrationId}/review`, payload)
  return data
}

export async function batchReview(payload) {
  const { data } = await apiClient.post('/reviews/batch', payload)
  return data
}

export async function verifySensitive(registrationId) {
  const { data } = await apiClient.get(`/registrations/${registrationId}/verify-sensitive`)
  return data
}

export async function promoteWaitlist(registrationId, payload = {}) {
  const { data } = await apiClient.patch(`/registrations/${registrationId}/waitlist-promote`, payload)
  return data
}

export async function listReviews(registrationId, params = {}) {
  const { data } = await apiClient.get(`/registrations/${registrationId}/reviews`, { params })
  return data
}
