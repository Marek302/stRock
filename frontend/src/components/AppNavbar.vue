<script setup lang="ts">
import { useTemplateRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBubble } from '../composables/useBubble'

const sections = ['Carte', 'Publications', 'Messages'] as const
const route = useRoute()
const router = useRouter()
const navbar = useTemplateRef<HTMLElement>('navbar')
const { activeIndex, bubbleStyle, attractBubble, resetBubble, selectBubble } =
  useBubble(navbar, sections.length, Number(route.meta.order ?? 0))

watch(() => route.meta.order, (order) => {
  selectBubble(Number(order ?? 0))
})

function selectSection(index: number) {
  selectBubble(index)
  if (index === 0) void router.push({ name: 'map' })
  if (index === 1) void router.push({ name: 'posts' })
  if (index === 2) void router.push({ name: 'messages' })
}
</script>

<template>
  <nav
    ref="navbar"
    class="navbar liquid-glass"
    aria-label="Navigation principale"
    @pointermove="attractBubble"
    @pointerleave="resetBubble"
    @pointercancel="resetBubble"
  >
    <span class="selection-bubble" :style="bubbleStyle" aria-hidden="true"></span>
    <button
      v-for="(section, index) in sections"
      :key="section"
      type="button"
      class="relative z-10 flex h-full min-w-0 flex-1 cursor-pointer items-center justify-center px-3 pb-[env(safe-area-inset-bottom,0px)] text-sm font-medium focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700 md:pb-0"
      :class="activeIndex === index ? 'text-slate-900' : 'text-slate-700'"
      :aria-pressed="activeIndex === index"
      @click="selectSection(index)"
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
  isolation: isolate;
  position: fixed;
  z-index: 1000;
  bottom: 0;
  left: 0;
  width: 100%;
  height: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px));
  border-radius: 24px 24px 0 0;
}

.selection-bubble {
  position: absolute;
  inset: 0 auto 0 0;
  pointer-events: none;
  border: 1px solid rgb(255 255 255 / 75%);
  border-radius: 999px;
  background: linear-gradient(135deg, rgb(255 255 255 / 60%), rgb(225 242 255 / 28%));
  box-shadow: inset 0 2px 5px rgb(255 255 255 / 80%), inset 0 -2px 6px rgb(137 179 211 / 20%), 0 2px 12px rgb(31 72 106 / 10%);
  transition: transform 420ms cubic-bezier(0.22, 1.2, 0.36, 1);
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

@media (prefers-reduced-motion: reduce) {
  .selection-bubble {
    transform: var(--bubble-resting-transform) !important;
    transition: none;
  }
}
</style>
