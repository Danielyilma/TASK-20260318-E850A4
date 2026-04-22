<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: import.meta.env.VITE_DEV_ADMIN_USERNAME ?? '',
  password: '',
})

const errors = reactive({
  username: '',
  password: '',
})

const touched = ref(false)

function validate() {
  errors.username = form.username.trim() ? '' : 'Username is required'
  errors.password = form.password ? '' : 'Password is required'
  return !errors.username && !errors.password
}

async function submit() {
  touched.value = true
  if (!validate()) return
  try {
    await auth.login(form.username.trim(), form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect.startsWith('/') && !redirect.startsWith('//')) {
      await router.replace(redirect)
    } else {
      await router.replace({ name: 'activities' })
    }
  } catch {
    // auth.error set in store
  }
}

onMounted(() => {
  auth.restoreSession()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <h1>Sign in</h1>
      <p class="subhead">Authenticate with the live API. Invalid credentials return 401 from the server.</p>
    </header>

    <div class="card">
      <p class="muted">
        Authentication requires configured credentials. See your <code>.env</code> file.
      </p>

      <label class="field">
        <span>Username</span>
        <input v-model="form.username" name="username" autocomplete="username" />
        <small v-if="touched && errors.username" class="err">{{ errors.username }}</small>
      </label>

      <label class="field">
        <span>Password</span>
        <input v-model="form.password" name="password" type="password" autocomplete="current-password" />
        <small v-if="touched && errors.password" class="err">{{ errors.password }}</small>
      </label>

      <p v-if="auth.error" class="err" role="alert">{{ auth.error }}</p>

      <button class="btn primary" type="button" :disabled="auth.loading" @click="submit">
        {{ auth.loading ? 'Signing in…' : 'Sign in' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.page-header {
  margin-bottom: 1rem;
}
h1 {
  margin: 0 0 0.35rem;
}
.subhead {
  margin: 0;
  color: #4b5563;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.1rem;
  background: #fafafa;
  max-width: 420px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0.75rem 0;
}
input {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.55rem 0.65rem;
  font: inherit;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 0.55rem 0.85rem;
  font-weight: 700;
  cursor: pointer;
  margin-top: 0.5rem;
}
.btn.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.muted {
  color: #6b7280;
  font-size: 0.9rem;
}
.err {
  color: #b91c1c;
  margin: 0.25rem 0 0;
}
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}
</style>
