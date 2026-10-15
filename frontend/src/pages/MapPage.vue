<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import type { Map } from 'leaflet'
import MapPost from '../components/MapPost.vue'
import BackgroundMap from '../components/BackgroundMap.vue'
import { usePostLocations } from '../composables/usePostLocations'

const { locations, isLoading, error, reload } = usePostLocations()
const mapInstance = shallowRef<Map | null>(null)
const positionedPosts = computed(() => locations.value.filter(
  (post): post is { id: string; latitude: number; longitude: number } =>
    post.latitude != null && post.longitude != null
    && Number.isFinite(post.latitude) && Number.isFinite(post.longitude)
    && Math.abs(post.latitude) <= 90 && Math.abs(post.longitude) <= 180,
))
</script>

<template>
  <main id="carte" class="page" tabindex="-1" :aria-busy="isLoading">
    <BackgroundMap @ready="mapInstance = $event" />
    <template v-if="mapInstance">
      <MapPost
        v-for="post in positionedPosts"
        :key="post.id"
        :map="mapInstance"
        :latitude="post.latitude"
        :longitude="post.longitude"
      />
    </template>
    <div v-if="error" class="liquid-glass absolute left-4 top-4 z-[1000] max-w-[calc(100%-112px)] rounded-2xl p-4 text-sm text-slate-800" role="alert">
      <p>{{ error }}</p>
      <button type="button" class="mt-2 min-h-11 cursor-pointer rounded-lg px-3 font-medium underline" @click="reload">
        Réessayer
      </button>
    </div>
  </main>
</template>
