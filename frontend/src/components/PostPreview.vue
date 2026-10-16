<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { getPost, getNearestPostAddress } from '../api/posts'
import type { CommunityPost } from '../types/post'

const props = defineProps<{ postId: string }>()
const emit = defineEmits<{ close: [] }>()

const post = ref<CommunityPost | null>(null)
const address = ref<string | null>(null)
const addressSource = ref<'saved' | 'openstreetmap' | null>(null)
const addressUnavailable = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
const retry = ref(0)
const coordinateLabel = /^lat:\s*-?\d+(?:\.\d+)?,\s*lon:\s*-?\d+(?:\.\d+)?$/i

watch([() => props.postId, retry], async (_value, _previous, onCleanup) => {
  const controller = new AbortController()
  onCleanup(() => controller.abort())
  post.value = null
  address.value = null
  addressSource.value = null
  addressUnavailable.value = false
  error.value = null
  loading.value = true
  try {
    const loadedPost = await getPost(props.postId, controller.signal)
    post.value = loadedPost
    loading.value = false

    const savedLocation = loadedPost.location?.trim()
    if (savedLocation && !coordinateLabel.test(savedLocation)) {
      address.value = savedLocation
      addressSource.value = 'saved'
    } else if (loadedPost.latitude != null && loadedPost.longitude != null) {
      try {
        const nearest = await getNearestPostAddress(props.postId, controller.signal)
        if (!controller.signal.aborted) {
          address.value = nearest.address.trim() || null
          addressSource.value = nearest.source
          addressUnavailable.value = !address.value
        }
      } catch {
        if (!controller.signal.aborted) addressUnavailable.value = true
      }
    } else {
      addressUnavailable.value = true
    }
  } catch (cause) {
    if (!controller.signal.aborted) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de charger la publication.'
    }
  } finally {
    if (!controller.signal.aborted) loading.value = false
  }
}, { immediate: true })
</script>

<template>
  <section class="map-post-card" aria-label="Aperçu de la publication" @click.stop @dblclick.stop @keydown.esc.stop="emit('close')">
    <button type="button" class="close-preview" aria-label="Fermer l’aperçu" @click="emit('close')">×</button>
    <p v-if="loading" role="status">Chargement…</p>
    <div v-else-if="error" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="retry-preview" @click="retry++">Réessayer</button>
    </div>
    <template v-else-if="post">
      <p v-if="post.content_type === 'safety_alert'" class="text-sm font-semibold text-red-700">Signalement</p>
      <h2 class="preview-title">{{ post.title }}</h2>
      <p class="preview-description">{{ post.description }}</p>
      <p v-if="address" class="preview-address">
        {{ address }}
        <small v-if="addressSource === 'openstreetmap'" class="address-credit">© OpenStreetMap contributors</small>
      </p>
      <p v-else-if="addressUnavailable" class="preview-address">Adresse indisponible</p>
      <RouterLink v-if="post.content_type !== 'safety_alert'" class="view-post" :to="{ name: 'posts', query: { post: postId } }">Voir la publication</RouterLink>
    </template>
  </section>
</template>

<style scoped>
.map-post-card {
  position: absolute;
  top: 24px;
  left: 24px;
  width: min(280px, calc(100vw - 32px));
  max-height: min(320px, calc(100dvh - 200px));
  overflow-y: auto;
  padding: 20px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: white;
  box-shadow: 0 8px 28px rgb(15 23 42 / 20%);
  color: #0f172a;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  cursor: default;
  overflow-wrap: anywhere;
  transform: translate(-50%, -50%);
  transform-origin: center;
  animation: preview-open 340ms ease-out both;
}

@keyframes preview-open {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9);
  }
  72% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.025);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.map-post-card.post-preview-leave-active {
  pointer-events: none;
  animation: preview-open 340ms ease-in reverse both;
}

@media (prefers-reduced-motion: reduce) {
  .map-post-card,
  .map-post-card.post-preview-leave-active {
    animation: none;
  }
}

.close-preview {
  position: absolute;
  top: 0;
  right: 0;
  width: 44px;
  height: 44px;
  cursor: pointer;
  font-size: 24px;
}

.preview-title {
  margin: 0 24px 12px 0;
  font-size: 16px;
  font-weight: 700;
}

.preview-description {
  max-height: 144px;
  overflow-y: auto;
  margin: 0 0 8px;
  white-space: pre-line;
  color: #475569;
}

.preview-address {
  margin: 0 0 16px;
  color: #334155;
}

.address-credit {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 11px;
}

.view-post {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 10px 16px;
  border-radius: 8px;
  background: #2563eb;
  color: white;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}

.view-post:hover {
  background: #1d4ed8;
}

.retry-preview {
  min-height: 44px;
  cursor: pointer;
  text-decoration: underline;
}

.close-preview:focus-visible,
.view-post:focus-visible,
.retry-preview:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}
</style>
