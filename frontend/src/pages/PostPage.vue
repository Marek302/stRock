<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import Post from '../components/Post.vue'
import { getPosts } from '../api/posts'
import { API_BASE_URL } from '../api/client'
import type { CommunityPost } from '../types/post'

const posts = ref<CommunityPost[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const hasMore = ref(true)
const controller = new AbortController()

async function loadMore() {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    const result = await getPosts(posts.value.length, 20, controller.signal)
    posts.value.push(...result.posts)
    hasMore.value = result.posts.length === result.limit
  } catch (cause) {
    if (!controller.signal.aborted) {
      error.value = cause instanceof Error ? cause.message : 'Impossible de charger les publications.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadMore)
onBeforeUnmount(() => controller.abort())
</script>

<template>
  <main class="page posts-page bg-slate-50" aria-label="Publications">
    <div class="post-feed focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700" role="region" aria-label="Fil de publications" tabindex="0">
      <Post
        v-for="post in posts"
        :key="post.id"
        :title="post.title"
        :description="post.description"
        :user-id="post.user_id"
        :location="post.location ?? undefined"
        :starts-at="post.starts_at ?? undefined"
        :ends-at="post.ends_at ?? undefined"
        :image-url="post.images[0] ? `${API_BASE_URL}/images/${post.images[0].id}` : undefined"
      />
      <div class="mx-auto max-w-[640px] px-6 py-8 text-center" aria-live="polite">
        <p v-if="loading" role="status">Chargement des publications…</p>
        <template v-else-if="error">
          <p role="alert">{{ error }}</p>
          <button type="button" class="mt-3 min-h-11 cursor-pointer underline" @click="loadMore">Réessayer</button>
        </template>
        <p v-else-if="posts.length === 0">Aucune publication pour le moment.</p>
        <button v-else-if="hasMore" type="button" class="min-h-11 cursor-pointer underline" @click="loadMore">Voir plus de publications</button>
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

@media (min-width: 768px) {
  .posts-page {
    padding-top: 112px;
    padding-bottom: 0;
  }
}
</style>
