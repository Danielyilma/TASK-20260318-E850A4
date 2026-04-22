<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  label: { type: String, default: '' },
  variant: { type: String, default: 'primary' },
  disabled: { type: Boolean, default: false },
})
</script>

<template>
  <button type="button" class="lb" :class="variant" :disabled="disabled || loading">
    <span v-if="loading" class="spinner" aria-hidden="true" />
    <span><slot>{{ label }}</slot></span>
  </button>
</template>

<style scoped>
.lb {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  padding: 0.5rem 0.85rem;
  font-weight: 700;
  cursor: pointer;
  background: #fff;
}
.lb.primary {
  background: #2563eb;
  border-color: #1d4ed8;
  color: #fff;
}
.lb:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.spinner {
  width: 1em;
  height: 1em;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.lb:not(.primary) .spinner {
  border-color: #e5e7eb;
  border-top-color: #2563eb;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
