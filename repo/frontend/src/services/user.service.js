import { apiClient } from './api'

export async function listUsers(params = {}) {
  const { data } = await apiClient.get('/users', { params })
  return data
}

export async function createUser(payload) {
  const { data } = await apiClient.post('/users', payload)
  return data
}

export async function getUser(userId) {
  const { data } = await apiClient.get(`/users/${userId}`)
  return data
}

export async function updateUser(userId, payload) {
  const { data } = await apiClient.put(`/users/${userId}`, payload)
  return data
}

export async function deactivateUser(userId) {
  const { data } = await apiClient.delete(`/users/${userId}`)
  return data
}

export async function unlockUser(userId) {
  const { data } = await apiClient.post(`/users/${userId}/unlock`)
  return data
}
