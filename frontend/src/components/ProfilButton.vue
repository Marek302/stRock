<script setup lang="ts">
import User from '@primeicons/vue/user'
</script>

<template>
  <button type="button" class="profil-button liquid-glass" aria-label="Profil">
    <User size="70%" aria-hidden="true" />
  </button>
</template>

<style scoped>
.profil-button {
  display: grid;
  place-items: center;
  padding: 0;
  color: #334155;
  position: fixed;
  z-index: 1000;
  top: max(16px, env(safe-area-inset-top, 0px));
  right: max(16px, env(safe-area-inset-right, 0px));
  width: 64px;
  height: 64px;
  border-radius: 50%;
  cursor: pointer;
  transform: scale(1);
  transition: transform 420ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.profil-button :deep(svg) {
  width: 70%;
  height: 70%;
}

.profil-button:focus-visible {
  outline: 2px solid #0369a1;
  outline-offset: 3px;
}

@media (hover: hover) and (pointer: fine) {
  .profil-button:hover {
    transform: scale(1.06, 1.04);
  }
}

.profil-button:active {
  transform: scale(0.94);
  transition-duration: 100ms;
}

@media (prefers-reduced-motion: reduce) {
  .profil-button,
  .profil-button:hover,
  .profil-button:active {
    transform: none;
    transition: none;
  }
}

@media (min-width: 768px) {
  .profil-button {
    top: 18px;
    right: max(24px, env(safe-area-inset-right, 0px));
    width: 80px;
    height: 80px;
  }
}
</style>
