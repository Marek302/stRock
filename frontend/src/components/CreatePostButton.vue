<script setup lang="ts">
import Plus from '@primeicons/vue/plus'

const emit = defineEmits<{ click: [] }>()
</script>

<template>
  <button type="button" class="create-post-button spring-button" aria-label="Créer une publication" @click="emit('click')">
    <Plus aria-hidden="true" />
  </button>
</template>

<style scoped>
.create-post-button {
  position: absolute;
  z-index: 10;
  right: max(16px, env(safe-area-inset-right, 0px));
  bottom: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px) + 16px);
  display: grid;
  place-items: center;
  width: 88px;
  height: 88px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgb(37 99 235 / 80%);
  color: white;
  box-shadow: 0 4px 14px rgb(15 23 42 / 18%);
  cursor: pointer;
}

.create-post-button :deep(svg.p-icon) {
  width: 30px;
  height: 30px;
}

.create-post-button:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 3px;
}

@media (min-width: 768px) {
  .create-post-button {
    right: max(24px, env(safe-area-inset-right, 0px));
    bottom: max(24px, env(safe-area-inset-bottom, 0px));
  }
}
</style>
