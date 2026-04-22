import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import App from '../App.vue'
import router from '../router'
import { useNetworkStore } from '../stores/network'

describe('App.vue', () => {
  it('mounts successfully with router and pinia', () => {
    const pinia = createPinia()
    const wrapper = mount(App, {
      global: {
        plugins: [pinia, router],
        stubs: {
          RouterView: { template: '<div class="router-view-stub" />' },
        },
      },
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.app-shell').exists()).toBe(true)
  })

  it('shows offline banner when network store is offline', () => {
    const pinia = createPinia()
    const net = useNetworkStore(pinia)
    net.setOnline(false)
    const wrapper = mount(App, {
      global: {
        plugins: [pinia, router],
        stubs: {
          RouterView: { template: '<div class="router-view-stub" />' },
        },
      },
    })
    expect(wrapper.text()).toContain('You are offline')
  })
})
