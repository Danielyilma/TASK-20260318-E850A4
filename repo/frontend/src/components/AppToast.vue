<script setup>
import { storeToRefs } from 'pinia'
import { useToastStore } from '../stores/toast'

const toast = useToastStore()
const { items } = storeToRefs(toast)
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <div
      v-for="t in items"
      :key="t.id"
      class="toast"
      :class="t.variant"
      role="status"
    >
      <div class="toast-title">{{ t.title }}</div>
      <div class="toast-msg">{{ t.message }}</div>
      <button type="button" class="toast-close" @click="toast.dismiss(t.id)">×</button>
    </div>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: min(420px, calc(100vw - 2rem));
}
.toast {
  position: relative;
  border-radius: 10px;
  padding: 0.75rem 2rem 0.75rem 0.85rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  border: 1px solid #e5e7eb;
  background: #fff;
}
.toast.error {
  border-color: #fecaca;
  background: #fef2f2;
}
.toast-title {
  font-weight: 800;
  font-size: 0.85rem;
  color: #991b1b;
}
.toast-msg {
  font-size: 0.9rem;
  color: #374151;
  margin-top: 0.2rem;
}
.toast-close {
  position: absolute;
  top: 0.35rem;
  right: 0.35rem;
  border: none;
  background: transparent;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}
</style>
