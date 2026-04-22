import { describe, it, expect, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import router from '../router/index.js'
import { useAuthStore } from '../stores/auth'

describe('router guards', () => {
  afterEach(() => {
    localStorage.removeItem('arfamp_access_token')
  })

  it('redirects unauthenticated visitors from /activities to login', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    await router.push('/')
    await router.isReady()
    await router.push('/activities')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/activities')
  })

  it('redirects applicants away from /admin/users', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const auth = useAuthStore()
    auth.$patch({
      accessToken: 'test-token',
      user: { id: '1', username: 'u', role: 'applicant', created_at: '2026-01-01T00:00:00Z' },
    })
    localStorage.setItem('arfamp_access_token', 'test-token')

    await router.push('/')
    await router.isReady()
    await router.push('/admin/users')
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('home')
  })
})
