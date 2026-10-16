<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import type { Map } from 'leaflet'
import { useRoute, useRouter } from 'vue-router'
import MapPost from '../components/MapPost.vue'
import BackgroundMap from '../components/BackgroundMap.vue'
import { usePostLocations } from '../composables/usePostLocations'
import { containsPoint } from '../maps/geometry'
import { saintRochRings } from '../maps/saintRoch'

const { locations, isLoading, error, reload } = usePostLocations()
const route = useRoute()
const router = useRouter()
const isPickingLocation = computed(() => route.name === 'map' && route.query.pickPostLocation === '1')
const locationError = ref<string | null>(null)
const mapInstance = shallowRef<Map | null>(null)
const selectedPostId = ref<string | null>(null)
const requestedPostId = computed(() => route.name === 'map' && typeof route.query.post === 'string'
  ? route.query.post : null)
const activePostId = computed(() => requestedPostId.value || selectedPostId.value)

function selectPreview(postId: string) {
  selectedPostId.value = postId
  void router.replace({ name: 'map', query: {
    ...route.query, post: postId, latitude: undefined, longitude: undefined,
  } })
}

function closePreview() {
  selectedPostId.value = null
  if (requestedPostId.value) {
    void router.replace({ name: 'map', query: {
      ...route.query, post: undefined, latitude: undefined, longitude: undefined,
    } })
  }
}

watch(mapInstance, (map, _previous, onCleanup) => {
  if (!map) return
  const onMapClick = (event: { latlng: { lat: number; lng: number } }) => {
    if (!isPickingLocation.value) {
      closePreview()
      return
    }
    const { lat, lng } = event.latlng
    if (!containsPoint([lng, lat], saintRochRings)) {
      locationError.value = 'Choisissez un point dans le quartier Saint-Roch.'
      return
    }
    locationError.value = null
    void router.push({
      name: 'posts',
      query: { resumePost: '1', latitude: String(lat), longitude: String(lng) },
    })
  }
  map.on('click', onMapClick)
  onCleanup(() => map.off('click', onMapClick))
})
watch(isPickingLocation, (picking) => {
  locationError.value = null
  if (picking) selectedPostId.value = null
})
watch(() => route.name, (name, previous) => {
  if (name === 'map' && previous !== 'map') void reload()
  if (name !== 'map') selectedPostId.value = null
})
const linkedLocation = computed(() => {
  if (!requestedPostId.value || typeof route.query.latitude !== 'string'
    || typeof route.query.longitude !== 'string') return null
  const latitude = Number(route.query.latitude)
  const longitude = Number(route.query.longitude)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)
    || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return null
  return { id: requestedPostId.value, latitude, longitude }
})
const positionedPosts = computed(() => {
  const posts = locations.value.filter(
    (post): post is { id: string; latitude: number; longitude: number } =>
      post.latitude != null && post.longitude != null
      && Number.isFinite(post.latitude) && Number.isFinite(post.longitude)
      && Math.abs(post.latitude) <= 90 && Math.abs(post.longitude) <= 180,
  )
  const linked = linkedLocation.value
  if (linked && !posts.some(post => post.id === linked.id)) {
    return [...posts, linked]
  }
  return posts
})
const selectedLocation = computed(() => positionedPosts.value.find(post => post.id === activePostId.value))
let centeredPostId: string | null = null
let centeredMap: Map | null = null

watch(
  [mapInstance, selectedLocation, activePostId, isPickingLocation, () => route.name],
  ([map, post, postId, picking, page]) => {
    if (page !== 'map' || picking || !postId) {
      centeredPostId = null
      return
    }
    if (!map || !post || (centeredMap === map && centeredPostId === postId)) return

    // Centrer une seule fois, puis laisser la carte libre au déplacement.
    map.invalidateSize({ pan: false })
    const target: [number, number] = [post.latitude, post.longitude]
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      map.setView(target, map.getZoom(), { animate: false })
    } else {
      map.flyTo(target, map.getZoom(), { animate: true, duration: 0.8 })
    }
    centeredMap = map
    centeredPostId = postId
  },
  { immediate: true, flush: 'post' },
)
</script>

<template>
  <main id="carte" class="page" tabindex="-1" :aria-busy="isLoading">
    <BackgroundMap @ready="mapInstance = $event" />
    <template v-if="mapInstance && !isPickingLocation">
      <MapPost
        v-for="post in positionedPosts"
        :key="post.id"
        :map="mapInstance"
        :post-id="post.id"
        :selected="activePostId === post.id"
        @select="selectPreview(post.id)"
        @close="closePreview"
        :latitude="post.latitude"
        :longitude="post.longitude"
      />
    </template>
    <div v-if="isPickingLocation" class="location-picker-panel">
      <p>Appuyez sur la carte pour placer votre publication dans Saint-Roch.</p>
      <p v-if="locationError" role="alert">{{ locationError }}</p>
      <button type="button" @click="router.push({ name: 'posts', query: { resumePost: '1' } })">Retour à la publication</button>
    </div>
    <div v-if="error" class="liquid-glass absolute left-4 top-4 z-[1000] max-w-[calc(100%-112px)] rounded-2xl p-4 text-sm text-slate-800" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="mt-2 min-h-11 cursor-pointer rounded-lg px-3 font-medium underline" @click="reload">
        Réessayer
      </button>
    </div>
  </main>
</template>

<style scoped>
.location-picker-panel {
  position: absolute;
  z-index: 1000;
  top: 16px;
  left: 16px;
  max-width: min(360px, calc(100% - 32px));
  padding: 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 12px rgb(0 0 0 / 15%);
}

.location-picker-panel p { margin: 0 0 8px; }
.location-picker-panel button { color: #2563eb; cursor: pointer; }
</style>
