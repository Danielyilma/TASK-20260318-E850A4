<script setup>
defineProps({
  padded: { type: Boolean, default: true },
})
</script>

<template>
  <div class="default-layout" :class="{ padded }">
    <slot />
  </div>
</template>

<style scoped>
.default-layout {
  width: 100%;
}
.default-layout.padded {
  padding: 0;
}
</style>
