<script setup lang="ts">
import { onBeforeUnmount, onMounted, shallowRef, watch } from 'vue'
import { divIcon, marker, type Map, type Marker } from 'leaflet'
import MapMarker from '@primeicons/vue/map-marker'

const props = defineProps<{
  map: Map
  latitude: number
  longitude: number
}>()

const target = shallowRef<HTMLElement | null>(null)
let instance: Marker | undefined

onMounted(() => {
  const element = document.createElement('div')
  instance = marker([props.latitude, props.longitude], {
    icon: divIcon({ html: element, className: '', iconSize: [48, 48], iconAnchor: [24, 24] }),
    interactive: false,
    keyboard: false,
  }).addTo(props.map)
  target.value = element
})

watch(() => [props.latitude, props.longitude], () => {
  instance?.setLatLng([props.latitude, props.longitude])
})

onBeforeUnmount(() => instance?.remove())
</script>

<template>
  <Teleport v-if="target" :to="target">
    <div class="map-post" role="img" aria-label="Position d’une publication">
      <MapMarker size="24" aria-hidden="true" />
    </div>
  </Teleport>
</template>

<style scoped>
.map-post {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgb(59 130 246 / 40%);
  color: #1d4ed8;
}
</style>
