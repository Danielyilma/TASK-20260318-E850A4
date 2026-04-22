import { apiClient } from './api'

export async function login(username, password) {
  const { data } = await apiClient.post('/auth/login', { username, password })
  return data
}

export async function logout() {
  const { data } = await apiClient.post('/auth/logout')
  return data
}

export async function fetchMe() {
  const { data } = await apiClient.get('/auth/me')
  return data
}

export async function updateMe(payload) {
  const { data } = await apiClient.put('/auth/me', payload)
  return data
}

export async function changePassword(currentPassword, newPassword) {
  const { data } = await apiClient.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}
