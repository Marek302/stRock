<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getPost } from '../api/posts'
import type { PostItem } from '../types/post'
import Post from '../components/Post.vue'
import { toPostItem, usePosts } from '../composables/usePosts'

const { posts, isLoading, error, hasMore, reload, loadMore, loadOnScroll } = usePosts()
const route = useRoute()
const selectedPost = ref<PostItem | null>(null)
const selectedLoading = ref(false)
const selectedError = ref<string | null>(null)
const feedElement = ref<HTMLElement | null>(null)
const displayedPosts = computed(() => selectedPost.value
  ? [selectedPost.value, ...posts.value.filter(post => post.id !== selectedPost.value?.id)]
  : posts.value)

watch(() => route.name === 'posts' ? route.query.post : undefined, async (id, _previous, onCleanup) => {
  selectedPost.value = null
  selectedError.value = null
  selectedLoading.value = false
  if (typeof id !== 'string' || !id) return
  const controller = new AbortController()
  onCleanup(() => controller.abort())
  selectedLoading.value = true
  try {
    selectedPost.value = toPostItem(await getPost(id, controller.signal))
    await nextTick()
    feedElement.value?.scrollTo({ top: 0 })
    feedElement.value?.querySelector<HTMLElement>('[data-selected="true"]')?.focus({ preventScroll: true })
  } catch (cause) {
    if (!controller.signal.aborted) {
      selectedError.value = cause instanceof Error ? cause.message : 'Impossible de charger la publication.'
    }
  } finally {
    if (!controller.signal.aborted) selectedLoading.value = false
  }
}, { immediate: true })
</script>

<template>
  <main class="page posts-page bg-slate-50" aria-label="Publications" :aria-busy="isLoading || selectedLoading">
    <div ref="feedElement" class="post-feed focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700" role="region" aria-label="Fil de publications" tabindex="0" @scroll.passive="loadOnScroll">
      <p v-if="selectedLoading" class="p-6 text-center text-slate-600" role="status">Chargement de la publication…</p>
      <div v-if="selectedError" class="p-6 text-center text-red-700" role="alert">
        <p>{{ selectedError }}</p>
        <RouterLink :to="{ name: 'posts' }" class="mt-3 inline-block min-h-11 underline">Voir toutes les publications</RouterLink>
      </div>
      <Post
        v-for="post in displayedPosts"
        :key="post.id"
        :data-selected="post.id === selectedPost?.id"
        :class="{ 'selected-post': post.id === selectedPost?.id }"
        tabindex="-1"
        :title="post.title"
        :description="post.description"
        :user-id="post.userId"
        :image-url="post.imageUrl"
        :location="post.location"
        :starts-at="post.startsAt"
        :ends-at="post.endsAt"
      />
      <div v-if="isLoading || error || !hasMore" class="feed-status p-6 text-center text-slate-600">
        <p v-if="isLoading" role="status">Chargement des publications…</p>
        <div v-else-if="error" role="alert">
          <p>{{ error }}</p>
          <button type="button" class="mt-3 min-h-11 cursor-pointer rounded-lg px-4 font-medium underline" @click="posts.length ? loadMore() : reload()">
            Réessayer
          </button>
        </div>
        <p v-else-if="!displayedPosts.length" role="status">Aucune publication pour le moment.</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.posts-page {
  padding-top: calc(72px + env(safe-area-inset-top, 0px));
  padding-bottom: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px));
}

.post-feed {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0 16px 24px;
  height: 100%;
  overflow-y: auto;
  overscroll-behavior-y: contain;
}

.post-feed > * {
  flex-shrink: 0;
}

.selected-post {
  outline: 2px solid #2563eb;
  outline-offset: -2px;
}

.feed-status {
  padding-top: 88px;
}

@media (min-width: 768px) {
  .posts-page {
    padding-top: 112px;
    padding-bottom: 0;
  }

  .feed-status {
    padding-top: 24px;
  }
}
</style>
