import { onMounted, ref } from 'vue'
import { API_BASE_URL } from '../api/client'
import { getPosts } from '../api/posts'
import type { PostItem } from '../types/post'

export function usePosts() {
  const posts = ref<PostItem[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const hasMore = ref(true)
  let nextSkip = 0

  async function loadPosts(reset = false) {
    if (isLoading.value) return

    isLoading.value = true
    error.value = null

    try {
      const result = await getPosts(reset ? 0 : nextSkip)
      const items = result.posts.map((post) => ({
        id: post.id,
        title: post.title,
        description: post.description,
        userId: post.user_id,
        imageUrl: post.first_image ? `${API_BASE_URL}/images/${post.first_image.id}` : undefined,
      }))

      posts.value = reset ? items : [...posts.value, ...items]
      nextSkip = result.skip + result.posts.length
      hasMore.value = result.posts.length === result.limit && result.limit > 0
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de charger les publications.'
    } finally {
      isLoading.value = false
    }
  }

  function reload() {
    return loadPosts(true)
  }

  function loadMore() {
    if (hasMore.value) return loadPosts()
  }

  function loadOnScroll(event: Event) {
    if (error.value) return

    const feed = event.currentTarget as HTMLElement
    const distanceToBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight
    if (distanceToBottom <= 200) void loadMore()
  }

  onMounted(reload)

  return { posts, isLoading, error, hasMore, reload, loadMore, loadOnScroll }
}
