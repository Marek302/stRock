<script setup lang="ts">
import Button from 'primevue/button'

const props = defineProps<{
  title: string
  description: string
  userId: string | number
}>()

const emit = defineEmits<{
  contact: [userId: string | number]
}>()
</script>

<template>
  <article class="post" :aria-label="title">
    <h2 class="text-center text-2xl font-semibold text-slate-900">{{ title }}</h2>
    <p class="mt-6 whitespace-pre-line text-base leading-relaxed text-slate-600">{{ description }}</p>
    <footer class="mt-auto pt-8">
      <Button class="min-h-11 w-full" label="Contact poster" @click="emit('contact', props.userId)" />
    </footer>
  </article>
</template>

<style scoped>
.post {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100%;
  margin-inline: auto;
  padding: 24px max(24px, env(safe-area-inset-right, 0px))
    24px max(24px, env(safe-area-inset-left, 0px));
  overflow-wrap: anywhere;
  border-bottom: 1px solid #e2e8f0;
  background: white;
  scroll-snap-align: start;
}

@media (min-width: 768px) {
  .post {
    max-width: 640px;
    padding: 32px;
    border-inline: 1px solid #e2e8f0;
  }
}
</style>
