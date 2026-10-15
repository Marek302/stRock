import { onMounted, ref } from 'vue'
import { getPostLocations } from '../api/posts'
import type { PostLocation } from '../types/post'

export function usePostLocations() {
  const locations = ref<PostLocation[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function reload() {
    if (isLoading.value) return

    isLoading.value = true
    error.value = null

    try {
      locations.value = await getPostLocations()
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de charger les positions des publications.'
    } finally {
      isLoading.value = false
    }
  }

  onMounted(reload)

  return { locations, isLoading, error, reload }
}
