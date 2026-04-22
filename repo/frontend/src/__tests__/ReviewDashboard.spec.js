import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ReviewDashboard from '../views/ReviewDashboard.vue'
import * as regApi from '../services/registration.service'

describe('ReviewDashboard.vue', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads registrations from the API on mount', async () => {
    setActivePinia(createPinia())
    vi.spyOn(regApi, 'listRegistrations').mockResolvedValue({
      items: [
        {
          id: '880e8400-e29b-41d4-a716-446655440020',
          applicant_id: '550e8400-e29b-41d4-a716-446655440000',
          activity_id: '770e8400-e29b-41d4-a716-446655440010',
          status: 'submitted',
          requested_funding: 2500,
          deadline: '2026-06-30T23:59:59Z',
          is_locked: false,
          created_at: '2026-03-20T10:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    })

    const wrapper = mount(ReviewDashboard)
    await flushPromises()

    expect(regApi.listRegistrations).toHaveBeenCalled()
    expect(wrapper.text()).toContain('880e8400-e29b-41d4-a716-446655440020')
    expect(wrapper.text()).toContain('submitted')
  })
})
