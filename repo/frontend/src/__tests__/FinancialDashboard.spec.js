import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FinancialDashboard from '../views/FinancialDashboard.vue'
import * as fundingApi from '../services/funding.service'

describe('FinancialDashboard.vue', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists funding accounts on mount', async () => {
    setActivePinia(createPinia())
    vi.spyOn(fundingApi, 'listFundingAccounts').mockResolvedValue({
      items: [
        {
          id: '110e8400-e29b-41d4-a716-446655440090',
          registration_id: '880e8400-e29b-41d4-a716-446655440020',
          approved_budget: 10000,
          total_income: 10000,
          total_expenses: 0,
          balance: 10000,
          is_overspent: false,
          created_at: '2026-04-01T14:30:00Z',
        },
      ],
      total: 1,
      page: 1,
      per_page: 100,
      pages: 1,
    })
    vi.spyOn(fundingApi, 'getFundingAccount').mockResolvedValue({
      id: '110e8400-e29b-41d4-a716-446655440090',
      registration_id: '880e8400-e29b-41d4-a716-446655440020',
      approved_budget: 10000,
      total_income: 10000,
      total_expenses: 0,
      balance: 10000,
      is_overspent: false,
      overspend_percentage: 0,
      created_at: '2026-04-01T14:30:00Z',
      updated_at: '2026-04-01T14:30:00Z',
    })
    vi.spyOn(fundingApi, 'listTransactions').mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 100,
      pages: 0,
    })

    const wrapper = mount(FinancialDashboard)
    await flushPromises()

    expect(fundingApi.listFundingAccounts).toHaveBeenCalled()
    expect(wrapper.text()).toContain('110e8400')
  })
})
