<script setup lang="ts">
import { useId } from 'vue'
import { useRouter } from 'vue-router'
import User from '@primeicons/vue/user'

const thinIconId = useId()
const router = useRouter()
</script>

<template>
  <button type="button" class="profil-button liquid-glass spring-button" :style="{ '--profile-icon-filter': `url(#${thinIconId})` }" aria-label="Profil" @click="router.push({ name: 'profile' })">
    <svg style="position: absolute; width: 0; height: 0" aria-hidden="true" focusable="false">
      <defs>
        <filter :id="thinIconId">
          <feMorphology operator="erode" radius="0.2" />
        </filter>
      </defs>
    </svg>
    <User size="70%" aria-hidden="true" />
  </button>
</template>

<style scoped>
.profil-button {
  display: grid;
  place-items: center;
  padding: 0;
  color: #334155;
  background: rgb(231 243 255 / 75%);
  position: fixed;
  z-index: 1000;
  top: max(16px, env(safe-area-inset-top, 0px));
  right: max(16px, env(safe-area-inset-right, 0px));
  width: 56px;
  height: 56px;
  border-radius: 50%;
  cursor: pointer;
}

.profil-button :deep(svg.p-icon) {
  width: 70%;
  height: 70%;
}

/* PrimeIcons uses filled outlines; erode their edges to thin the same icon. */
.profil-button :deep(.p-icon path) {
  filter: var(--profile-icon-filter);
}

.profil-button:focus-visible {
  outline: 2px solid #0369a1;
  outline-offset: 3px;
}

@media (min-width: 768px) {
  .profil-button {
    top: 18px;
    right: max(24px, env(safe-area-inset-right, 0px));
    width: 64px;
    height: 64px;
  }
}
</style>
