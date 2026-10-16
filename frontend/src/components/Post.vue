<script setup lang="ts">
import Button from 'primevue/button'

const props = defineProps<{
  postId: string
  title: string
  description: string
  hasLocation: boolean
  startsAt?: string
  endsAt?: string
  imageUrl?: string
  userId: string | number
}>()

function formatDate(value: string) {
  return new Intl.DateTimeFormat('fr-CA', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Toronto',
  }).format(new Date(value))
}

const emit = defineEmits<{
  contact: [userId: string | number]
  viewLocation: [postId: string]
}>()
</script>

<template>
  <article class="post" :aria-label="title">
    <h2 class="text-center text-2xl font-semibold text-slate-900">{{ title }}</h2>
    <p v-if="startsAt" class="mt-2 text-center text-sm text-slate-600">
      <time :datetime="startsAt">{{ formatDate(startsAt) }}</time>
      <template v-if="endsAt"> — <time :datetime="endsAt">{{ formatDate(endsAt) }}</time></template>
    </p>
    <img
      v-if="imageUrl"
      :src="imageUrl"
      :alt="title"
      class="mt-6 max-h-[50dvh] w-full shrink-0 rounded-lg object-contain"
      loading="lazy"
      decoding="async"
    />
    <p class="mt-6 whitespace-pre-line text-base leading-relaxed text-slate-600">{{ description }}</p>
    <footer class="pt-6">
      <Button v-if="hasLocation" class="mb-3 min-h-11 w-full" label="Voir le lieu" severity="secondary" @click="emit('viewLocation', props.postId)" />
      <Button class="min-h-11 w-full" label="Contacter l’auteur" @click="emit('contact', props.userId)" />
    </footer>
  </article>
</template>

<style scoped>
.post {
  display: flex;
  flex-direction: column;
  width: 100%;
  margin-inline: auto;
  padding: 24px max(24px, env(safe-area-inset-right, 0px))
    24px max(24px, env(safe-area-inset-left, 0px));
  overflow-wrap: anywhere;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: white;
}

@media (min-width: 768px) {
  .post {
    max-width: 640px;
    padding: 32px;
  }
}
</style>
