<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { DomEvent, divIcon, marker, type Map, type Marker } from 'leaflet'
import MapMarker from '@primeicons/vue/map-marker'
import { getPost } from '../api/posts'
import type { CommunityPost } from '../types/post'

const props = defineProps<{
  map: Map
  postId: string
  latitude: number
  longitude: number
  selected: boolean
}>()
const emit = defineEmits<{ select: []; close: [] }>()

const target = shallowRef<HTMLElement | null>(null)
const post = ref<CommunityPost | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const retry = ref(0)
let instance: Marker | undefined

onMounted(() => {
  const element = document.createElement('div')
  DomEvent.disableClickPropagation(element)
  DomEvent.disableScrollPropagation(element)
  instance = marker([props.latitude, props.longitude], {
    icon: divIcon({ html: element, className: '', iconSize: [48, 48], iconAnchor: [24, 24] }),
    interactive: true,
    keyboard: false,
  }).addTo(props.map)
  target.value = element
})

watch(() => [props.latitude, props.longitude], () => {
  instance?.setLatLng([props.latitude, props.longitude])
})

watch([() => props.selected, () => props.postId, retry], async ([selected], _previous, onCleanup) => {
  instance?.setZIndexOffset(selected ? 1000 : 0)
  if (!selected) return
  props.map.panInside([props.latitude, props.longitude], {
    paddingTopLeft: [150, 190], paddingBottomRight: [150, 180],
  })
  const controller = new AbortController()
  onCleanup(() => controller.abort())
  post.value = null
  error.value = null
  loading.value = true
  try {
    post.value = await getPost(props.postId, controller.signal)
  } catch (cause) {
    if (!controller.signal.aborted) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de charger la publication.'
    }
  } finally {
    if (!controller.signal.aborted) loading.value = false
  }
})

onBeforeUnmount(() => instance?.remove())
</script>

<template>
  <Teleport v-if="target" :to="target">
    <section v-if="selected" class="map-post-card" aria-label="Aperçu de la publication" @click.stop @dblclick.stop @keydown.esc.stop="emit('close')">
      <button type="button" class="close-preview" aria-label="Fermer l’aperçu" @click="emit('close')">×</button>
      <p v-if="loading" role="status">Chargement…</p>
      <div v-else-if="error" role="alert">
        <p>{{ error }}</p>
        <button type="button" class="retry-preview" @click="retry++">Réessayer</button>
      </div>
      <template v-else-if="post">
        <h2 class="preview-title">{{ post.title }}</h2>
        <p class="preview-description">{{ post.description }}</p>
        <RouterLink class="view-post" :to="{ name: 'posts', query: { post: postId } }">Voir la publication</RouterLink>
      </template>
    </section>
    <button v-else type="button" class="map-post" aria-label="Voir cette publication" @click.stop="emit('select')">
      <MapMarker size="24" aria-hidden="true" />
    </button>
  </Teleport>
</template>

<style scoped>
.map-post {
  cursor: pointer;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border: 0;
  border-radius: 50%;
  background: rgb(59 130 246 / 40%);
  color: #1d4ed8;
}

.map-post-card {
  position: absolute;
  top: 24px;
  left: 24px;
  transform: translate(-50%, -50%);
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
  margin: 0 0 16px;
  white-space: pre-line;
  color: #475569;
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

.map-post:focus-visible,
.close-preview:focus-visible,
.view-post:focus-visible,
.retry-preview:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}
</style>
