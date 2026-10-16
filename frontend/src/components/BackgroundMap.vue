<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { control, map, type Map } from 'leaflet'
import { SaintRochLayer, saintRochBounds } from '../maps/saintRoch'
import { constrainMovement } from '../maps/constrainMovement'
import 'leaflet/dist/leaflet.css'

const emit = defineEmits<{ ready: [map: Map] }>()

const saintRochCenter: [number, number] = [46.8145, -71.2235]
const initialZoom = 16

const container = ref<HTMLDivElement | null>(null)
let instance: Map | undefined
let resizeObserver: ResizeObserver | undefined
let removeMovementConstraint: (() => void) | undefined

onMounted(() => {
  if (!container.value) return

  instance = map(container.value, {
    zoomControl: false,
    inertia: false,
    scrollWheelZoom: 'center',
    doubleClickZoom: 'center',
    touchZoom: 'center',
    bounceAtZoomLimits: false,
    minZoom: 0,
    maxZoom: 19,
  })
  const startingZoom = Math.min(19, Math.max(initialZoom, instance.getBoundsZoom(saintRochBounds, true)))
  instance.setMinZoom(instance.getBoundsZoom(saintRochBounds))
  instance.setView(saintRochCenter, startingZoom)

  removeMovementConstraint = constrainMovement(instance)

  new SaintRochLayer({
    noWrap: true,
    keepBuffer: 2,
    minZoom: 0,
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> — contributeurs · Limites : <a href="https://www.donneesquebec.ca/recherche/dataset/5b1ae6f2-6719-46df-bd2f-e57a7034c917">Ville de Québec</a>',
  }).addTo(instance)

  const zoom = control.zoom({
    position: 'bottomright',
    zoomInTitle: 'Zoomer',
    zoomOutTitle: 'Dézoomer',
  }).addTo(instance)
  instance.attributionControl.getContainer()?.querySelector('a[href*="leafletjs.com"]')
    ?.setAttribute('title', 'Bibliothèque JavaScript de cartes interactives')
  zoom.getContainer()?.querySelector('.leaflet-control-zoom-in')?.setAttribute('aria-label', 'Zoomer')
  zoom.getContainer()?.querySelector('.leaflet-control-zoom-out')?.setAttribute('aria-label', 'Dézoomer')

  // Allow the whole neighborhood to fit on screen; navigation still stops at its polygon edges.
  const updateMinimumZoom = () => {
    if (!instance) return
    instance.invalidateSize({ pan: false })
    instance.setMinZoom(0)
    const minimumZoom = instance.getBoundsZoom(saintRochBounds)
    instance.setMinZoom(minimumZoom)
    if (instance.getZoom() < minimumZoom) instance.setZoom(minimumZoom, { animate: false })
  }

  updateMinimumZoom()
  resizeObserver = new ResizeObserver(updateMinimumZoom)
  resizeObserver.observe(container.value)
  emit('ready', instance)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  removeMovementConstraint?.()
  instance?.remove()
})
</script>

<template>
  <div ref="container" class="background-map" role="region" aria-label="Carte interactive du quartier Saint-Roch à Québec"></div>
</template>

<style scoped>
.background-map {
  position: absolute;
  inset: 0;
  background: #fff1f2;
  isolation: isolate;
}

.background-map :deep(.leaflet-bottom) {
  bottom: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px) + 8px);
}

.background-map :deep(.leaflet-right) {
  right: env(safe-area-inset-right, 0px);
}

.background-map :deep(.leaflet-control-zoom a) {
  width: 44px;
  height: 44px;
  line-height: 44px;
}

.background-map :deep(.leaflet-control-zoom) {
  margin-bottom: 16px;
}

@media (min-width: 768px) {
  .background-map :deep(.leaflet-bottom) {
    bottom: env(safe-area-inset-bottom, 0px);
  }
}

/* Preserve tile sizing when global media styles or Tailwind are applied. */
.background-map :deep(.leaflet-tile) {
  max-width: none;
  max-height: none;
}
</style>
