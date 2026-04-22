<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="nf">
    <h1>Page not found</h1>
    <p>The route you requested does not exist.</p>
    <RouterLink to="/">Back to home</RouterLink>
  </section>
</template>

<style scoped>
.nf {
  max-width: 560px;
}
h1 {
  margin-top: 0;
}
a {
  font-weight: 600;
}
</style>
