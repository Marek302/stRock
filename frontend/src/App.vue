<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppNavbar from './components/AppNavbar.vue'
import ProfilButton from './components/ProfilButton.vue'
import logo from '../logo/1.png'

const route = useRoute()
const transitionName = ref('page-slide-left')

watch(() => route.meta.order, (to, from) => {
  transitionName.value = Number(to ?? 0) > Number(from ?? 0) ? 'page-slide-left' : 'page-slide-right'
}, { flush: 'sync' })
</script>

<template>
  <div class="page-viewport">
    <RouterView v-slot="{ Component }">
      <Transition :name="transitionName">
        <KeepAlive exclude="LoginPage,ProfilePage">
          <component :is="Component" />
        </KeepAlive>
      </Transition>
    </RouterView>
  </div>
  <AppNavbar />
  <ProfilButton />
  <img :src="logo" class="app-logo" alt="roch-On!" />
</template>

<style>
.app-logo {
  position: fixed;
  z-index: 1000;
  top: max(16px, env(safe-area-inset-top, 0px));
  left: max(16px, env(safe-area-inset-left, 0px));
  width: 128px;
  height: auto;
  pointer-events: none;
}

.page-viewport {
  position: relative;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.page-viewport > .page {
  position: absolute;
  inset: 0;
}

.page-slide-left-enter-active,
.page-slide-left-leave-active,
.page-slide-right-enter-active,
.page-slide-right-leave-active {
  transition: transform 360ms cubic-bezier(0.22, 0.61, 0.36, 1);
  will-change: transform;
  pointer-events: none;
}

.page-slide-left-enter-from,
.page-slide-right-leave-to {
  transform: translateX(100%);
}

.page-slide-left-leave-to,
.page-slide-right-enter-from {
  transform: translateX(-100%);
}

@media (prefers-reduced-motion: reduce) {
  .page-slide-left-enter-active,
  .page-slide-left-leave-active,
  .page-slide-right-enter-active,
  .page-slide-right-leave-active {
    transition: none;
  }
}
</style>
