<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { CommunityPost } from '../types/post'
import LoadImage from './LoadImage.vue'
import AddLocalisation from './AddLocalisation.vue'
import DateSelectionButton from './dateSelectionButton.vue'
import { usePostCreation } from '../composables/usePostCreation'

const emit = defineEmits<{ close: []; created: [post: CommunityPost]; selectLocation: [] }>()
const panel = ref<HTMLElement | null>(null)
const titleInput = ref<HTMLInputElement | null>(null)
const { draft, error, needsLogin, isSubmitting, canEdit, canSubmit, publish } = usePostCreation()

onMounted(() => titleInput.value?.focus())

function requestClose() {
  if (!isSubmitting.value) emit('close')
}

function trapFocus(event: KeyboardEvent) {
  const elements = panel.value?.querySelectorAll<HTMLElement>('input:not(:disabled), textarea:not(:disabled), select:not(:disabled), button:not(:disabled), [role="spinbutton"][tabindex="0"], a[href]')
  if (!elements?.length) {
    event.preventDefault()
    panel.value?.focus()
    return
  }
  const first = elements[0]!
  const last = elements[elements.length - 1]!
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

async function submit() {
  const post = await publish()
  if (post) emit('created', post)
}
</script>

<template>
  <div class="post-creation-overlay" @click.self="requestClose">
    <section
      ref="panel"
      class="post-creation-panel"
      role="dialog"
      aria-modal="true"
      aria-label="Créer une publication"
      tabindex="-1"
      @keydown.esc.stop.prevent="requestClose"
      @keydown.tab="trapFocus"
    >
      <form class="post-creation-form" :aria-busy="isSubmitting" @submit.prevent="submit">
        <label class="post-creation-field">
          <span>Type</span>
          <select v-model="draft.contentType" :disabled="!canEdit">
            <option value="publication">Publication</option>
            <option value="safety_alert">Signalement</option>
          </select>
        </label>
        <p v-if="draft.contentType === 'safety_alert'" class="text-sm text-slate-600">
          Visible uniquement sur la carte pendant 2 heures, avec un repère rouge.
        </p>
        <label class="post-creation-field">
          <span>Titre</span>
          <input ref="titleInput" v-model="draft.title" type="text" minlength="3" maxlength="128" required :disabled="!canEdit" />
        </label>
        <label class="post-creation-field description-field">
          <span>Description</span>
          <textarea v-model="draft.description" minlength="1" maxlength="5000" required :disabled="!canEdit"></textarea>
        </label>
        <LoadImage :initial-file="draft.image" :disabled="!canEdit" @selected="draft.image = $event" />
        <AddLocalisation
          :disabled="!canEdit"
          :location="draft.location"
          :latitude="draft.latitude"
          :longitude="draft.longitude"
          :is-loading="draft.isResolvingLocation"
          @select="emit('selectLocation')"
        />
        <DateSelectionButton v-if="draft.contentType === 'publication'" v-model="draft.expirationHours" :disabled="!canEdit" />
        <div v-if="error" class="post-creation-error" role="alert">
          <p>{{ error }}</p>
          <RouterLink v-if="needsLogin" :to="{ name: 'login' }">Se connecter</RouterLink>
        </div>
        <button type="submit" class="publish-button" :disabled="!canSubmit">
          {{ isSubmitting ? 'Publication…' : 'Publier' }}
        </button>
      </form>
    </section>
  </div>
</template>

<style scoped>
.post-creation-overlay {
  position: fixed;
  z-index: 1100;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgb(15 23 42 / 35%);
}

.post-creation-panel {
  width: min(640px, calc(100vw - 32px), calc(100dvh - 32px));
  aspect-ratio: 1;
  padding: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: white;
  overflow-y: auto;
}

.post-creation-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.post-creation-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.post-creation-field input,
.post-creation-field textarea,
.post-creation-field select {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 8px;
}

.description-field {
  flex: 1;
}

.description-field textarea {
  flex: 1;
  min-height: 80px;
}

.post-creation-error {
  color: #b91c1c;
}

.post-creation-error p {
  margin: 0;
}

.publish-button {
  align-self: center;
  min-width: 180px;
  padding: 14px 40px;
  border: 0;
  border-radius: 6px;
  background: #2563eb;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
}
</style>
