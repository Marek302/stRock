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
  isReport?: boolean
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
  if (props.selected) instance.setZIndexOffset(1000)
})

watch(() => [props.latitude, props.longitude], () => {
  instance?.setLatLng([props.latitude, props.longitude])
})

watch(() => props.selected, (selected) => {
  instance?.setZIndexOffset(selected ? 1000 : 0)
})

onBeforeUnmount(() => instance?.remove())
</script>

<template>
  <Teleport v-if="target" :to="target">
    <Transition name="post-preview">
      <PostPreview v-if="selected" :post-id="postId" @close="emit('close')" />
    </Transition>
    <button v-if="!selected" type="button" class="map-post" :class="{ 'map-post--report': isReport }" :aria-label="isReport ? 'Voir ce signalement' : 'Voir cette publication'" @click.stop="emit('select')">
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
  background: #b1cdfb;
  color: #1d4ed8;
}

.map-post:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}

.map-post--report {
  background: #fecaca;
  color: #b91c1c;
}
.map-post--report:focus-visible {
  outline-color: #b91c1c;
}
</style>
