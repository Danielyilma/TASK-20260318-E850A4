import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useNetworkStore } from './stores/network'
import './style.css'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

useAuthStore(pinia).restoreSession()
useNetworkStore(pinia).init()

app.mount('#app')
