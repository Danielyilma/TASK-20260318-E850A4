import { apiClient } from './api'

export async function listActivities(params = {}) {
  const { data } = await apiClient.get('/activities', { params })
  return data
}

export async function getActivity(activityId) {
  const { data } = await apiClient.get(`/activities/${activityId}`)
  return data
}

export async function createActivity(payload) {
  const { data } = await apiClient.post('/activities', payload)
  return data
}

export async function updateActivity(activityId, payload) {
  const { data } = await apiClient.put(`/activities/${activityId}`, payload)
  return data
}

export async function deleteActivity(activityId) {
  const { data } = await apiClient.delete(`/activities/${activityId}`)
  return data
}
