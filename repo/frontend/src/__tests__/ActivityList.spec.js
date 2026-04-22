import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ActivityList from '../views/ActivityList.vue'
import { useAuthStore } from '../stores/auth'
import * as activityService from '../services/activity.service'
import * as authService from '../services/auth.service'

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/activities', name: 'activities', component: ActivityList },
      { path: '/activities/:id', name: 'activity-detail', component: { template: '<div />' } },
    ],
  })
}

describe('ActivityList.vue', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.removeItem('arfamp_access_token')
  })

  it('loads activities into the table after mount (API mocked for this unit test)', async () => {
    vi.spyOn(authService, 'fetchMe').mockResolvedValue({
      id: '550e8400-e29b-41d4-a716-446655440000',
      username: 'admin',
      role: 'system_admin',
      id_number: '****',
      contact_info: '****',
      is_locked: false,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })

    const listSpy = vi.spyOn(activityService, 'listActivities').mockResolvedValue({
      items: [
        {
          id: '770e8400-e29b-41d4-a716-446655440010',
          name: '2026 Community Development Grant',
          description: 'Annual grant',
          deadline: '2026-06-30T23:59:59Z',
          budget: 500000,
          is_active: true,
          created_at: '2026-03-01T09:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    })

    const pinia = createPinia()
    setActivePinia(pinia)

    const auth = useAuthStore(pinia)
    auth.$patch({
      accessToken: 'test-token',
      user: { id: '1', username: 'admin', role: 'system_admin', created_at: '2026-01-01T00:00:00Z' },
    })
    localStorage.setItem('arfamp_access_token', 'test-token')

    const router = createTestRouter()
    router.push('/activities')
    await router.isReady()

    const wrapper = mount(ActivityList, {
      global: {
        plugins: [pinia, router],
      },
    })

    await flushPromises()

    expect(listSpy).toHaveBeenCalled()
    expect(wrapper.text()).toContain('2026 Community Development Grant')
    expect(wrapper.findAll('tbody tr').length).toBeGreaterThan(0)
  })
})
