import { describe, it, expect, vi, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import { useAuthStore } from '../stores/auth'
import * as authService from '../services/auth.service'

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div />' } },
      { path: '/login', name: 'login', component: Login },
      { path: '/activities', name: 'activities', component: { template: '<div />' } },
    ],
  })
}

describe('Login.vue', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.removeItem('arfamp_access_token')
  })

  it('shows client-side validation errors when submitting empty fields', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)

    const router = createTestRouter()
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(Login, {
      global: {
        plugins: [pinia, router],
      },
    })

    await wrapper.get('input[name="username"]').setValue('')
    await wrapper.get('input[name="password"]').setValue('')
    await wrapper.get('button.btn.primary').trigger('click')
    await nextTick()

    const errs = wrapper.findAll('small.err').map((w) => w.text())
    expect(errs.some((t) => t.includes('Username is required'))).toBe(true)
    expect(errs.some((t) => t.includes('Password is required'))).toBe(true)
  })

  it('updates Pinia auth state after a successful login (axios mocked)', async () => {
    vi.spyOn(authService, 'login').mockResolvedValue({
      access_token: 'jwt-token',
      token_type: 'bearer',
      expires_at: '2026-12-31T00:00:00Z',
      user: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        username: 'admin',
        role: 'system_admin',
        created_at: '2026-01-01T00:00:00Z',
      },
    })

    const pinia = createPinia()
    setActivePinia(pinia)

    const router = createTestRouter()
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(Login, {
      global: {
        plugins: [pinia, router],
      },
    })

    await wrapper.get('input[name="username"]').setValue('admin')
    await wrapper.get('input[name="password"]').setValue('AdminP@ss1')
    await wrapper.get('button.btn.primary').trigger('click')
    await flushPromises()

    const auth = useAuthStore()
    expect(auth.accessToken).toBe('jwt-token')
    expect(auth.user?.username).toBe('admin')
    expect(localStorage.getItem('arfamp_access_token')).toBe('jwt-token')
  })
})
