<script setup lang="ts">
import { ref } from 'vue'

const sections = ['Map', 'Posts', 'Messages'] as const
const activeSection = ref<(typeof sections)[number]>('Map')
</script>

<template>
  <nav class="navbar" aria-label="Navigation principale">
    <button
      v-for="section in sections"
      :key="section"
      type="button"
      class="flex h-full min-w-0 flex-1 cursor-pointer items-center justify-center px-3 pb-[env(safe-area-inset-bottom,0px)] text-sm font-medium transition-colors duration-200 motion-reduce:transition-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700 md:pb-0"
      :class="activeSection === section ? 'bg-white/50 text-slate-900' : 'text-slate-700 hover:bg-white/25'"
      :aria-pressed="activeSection === section"
      @click="activeSection = section"
    >
      {{ section }}
    </button>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  align-items: stretch;
  overflow: hidden;
  position: fixed;
  z-index: 1000;
  bottom: 0;
  left: 0;
  width: 100%;
  height: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px));
  border: 1px solid rgb(255 255 255 / 60%);
  border-radius: 24px 24px 0 0;
  background: rgb(231 243 255 / 28%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
  backdrop-filter: blur(22px) saturate(160%);
  box-shadow: 0 4px 24px rgb(28 61 95 / 10%);
}

@media (min-width: 768px) {
  .navbar {
    top: 24px;
    bottom: auto;
    left: 50%;
    width: 420px;
    height: 68px;
    transform: translateX(-50%);
    border-radius: 999px;
  }
}
</style>
