<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import demoUsers from '../data/demo-users.json'

const props = defineProps<{
  title: string
  description: string
  location?: string
  startsAt?: string
  endsAt?: string
  imageUrl?: string
  contacting?: boolean
  contactDisabled?: boolean
  userId: string | number
}>()

const demoAuthor = computed(() => demoUsers.find(user => user.uid === props.userId))

function formatDate(value: string) {
  return new Intl.DateTimeFormat('fr-CA', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Toronto',
  }).format(new Date(value))
}

const emit = defineEmits<{
  contact: [userId: string | number]
}>()
</script>

<template>
  <article class="post" :aria-label="title">
    <h2 class="text-center text-2xl font-semibold text-slate-900">{{ title }}</h2>
    <div v-if="demoAuthor" class="mt-3 flex items-center justify-center gap-2 text-sm text-slate-500">
      <img v-if="demoAuthor.photoURL" :src="demoAuthor.photoURL" alt="" class="h-9 w-9 shrink-0 rounded-full object-cover" loading="lazy" />
      <span>Par {{ demoAuthor.displayName }}</span>
    </div>
    <p v-if="location" class="mt-4 text-center text-sm text-slate-600">{{ location }}</p>
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
      <Button class="min-h-11 w-full" label="Contacter l’auteur" :loading="contacting" :disabled="contactDisabled" @click="emit('contact', props.userId)" />
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
