import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import RegistrationWizard from '../views/RegistrationWizard.vue'

vi.mock('vue-router', () => ({
  RouterLink: { template: '<a><slot /></a>' },
  useRoute: () => ({
    name: 'registration-wizard',
    params: { registrationId: 'reg-1' },
    query: {},
  }),
  useRouter: () => ({ replace: vi.fn() }),
}))

vi.mock('../services/activity.service', () => ({
  getActivity: vi.fn().mockResolvedValue({ id: 'act-1', name: 'Activity A' }),
}))

vi.mock('../services/registration.service', () => ({
  getRegistration: vi.fn().mockResolvedValue({
    id: 'reg-1',
    activity_id: 'act-1',
    status: 'supplemented',
    is_locked: false,
    supplementary_deadline: '2030-01-01T00:00:00Z',
    form_data: {},
    requested_funding: 1000,
    deadline: '2030-01-01T00:00:00Z',
    supplementary_used: true,
  }),
  listChecklist: vi.fn().mockResolvedValue({
    items: [{ id: 'item-1', item_name: 'Doc', is_required: true, allowed_types: ['pdf'], max_file_size_mb: 20 }],
  }),
  listMaterialVersions: vi.fn().mockResolvedValue({
    checklist_item_id: 'item-1',
    item_name: 'Doc',
    versions: [],
  }),
  uploadMaterial: vi.fn(),
  patchMaterialVersionLabel: vi.fn(),
  downloadMaterialBlob: vi.fn(),
}))

describe('RegistrationWizard supplementary flow', () => {
  it('keeps upload controls visible for supplemented state', async () => {
    const wrapper = mount(RegistrationWizard)
    await flushPromises()
    expect(wrapper.find('input[type="file"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Supplementary window')
  })
})
