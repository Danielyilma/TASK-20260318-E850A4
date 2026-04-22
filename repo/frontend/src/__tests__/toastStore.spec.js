import { describe, it, expect, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AppToast from '../components/AppToast.vue'
import { useToastStore } from '../stores/toast'

describe('toast + AppToast', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('displays a pushed toast', async () => {
    const wrapper = mount(AppToast)
    const toast = useToastStore()
    toast.push({ title: 'NOT_FOUND', message: 'Missing resource', variant: 'error' })
    await flushPromises()
    expect(wrapper.text()).toContain('NOT_FOUND')
    expect(wrapper.text()).toContain('Missing resource')
  })
})
