<script setup lang="ts">
import { onBeforeUnmount, onMounted, shallowRef, watch } from 'vue'
import { DomEvent, divIcon, marker, type Map, type Marker } from 'leaflet'
import MapMarker from '@primeicons/vue/map-marker'
import PostPreview from './PostPreview.vue'

const props = defineProps<{
  map: Map
  postId: string
  latitude: number
  longitude: number
  selected: boolean
}>()
const emit = defineEmits<{ select: []; close: [] }>()

const target = shallowRef<HTMLElement | null>(null)
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

watch(() => props.selected, (selected) => {
  instance?.setZIndexOffset(selected ? 1000 : 0)
  if (!selected) return
  props.map.panInside([props.latitude, props.longitude], {
    paddingTopLeft: [150, 190], paddingBottomRight: [150, 180],
  })
})

onBeforeUnmount(() => instance?.remove())
</script>

<template>
  <Teleport v-if="target" :to="target">
    <PostPreview v-if="selected" :post-id="postId" @close="emit('close')" />
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

.map-post:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}
</style>
