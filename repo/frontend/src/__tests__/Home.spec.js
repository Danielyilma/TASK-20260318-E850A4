import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

function createRouterForHome() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: Home },
      { path: '/login', name: 'login', component: { template: '<div />' } },
      { path: '/activities', name: 'activities', component: { template: '<div />' } },
    ],
  })
}

vi.mock('../services/api', () => ({
  fetchHealth: vi.fn(),
}))

import { fetchHealth } from '../services/api'

describe('Home.vue', () => {
  let pinia

  beforeEach(() => {
    vi.clearAllMocks()
    pinia = createPinia()
    setActivePinia(pinia)
    fetchHealth.mockResolvedValue({ status: 'ok' })
  })

  it('loads health on mount via the API client', async () => {
    const router = createRouterForHome()
    await router.push('/')
    await router.isReady()
    mount(Home, { global: { plugins: [pinia, router] } })
    await flushPromises()

    expect(fetchHealth).toHaveBeenCalled()
  })

  it('refreshes health when the user clicks the button', async () => {
    const router = createRouterForHome()
    await router.push('/')
    await router.isReady()
    const wrapper = mount(Home, { global: { plugins: [pinia, router] } })
    await flushPromises()
    expect(fetchHealth).toHaveBeenCalledTimes(1)

    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(fetchHealth).toHaveBeenCalledTimes(2)
  })

  it('surfaces API error messages when the backend is unreachable', async () => {
    fetchHealth.mockRejectedValueOnce(new Error('network'))

    const router = createRouterForHome()
    await router.push('/')
    await router.isReady()
    const wrapper = mount(Home, { global: { plugins: [pinia, router] } })
    await flushPromises()

    expect(wrapper.text()).toContain('network')
  })
})
