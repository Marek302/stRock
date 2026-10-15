<script setup lang="ts">
import Post from '../components/Post.vue'
import { usePosts } from '../composables/usePosts'

const { posts, isLoading, error, hasMore, reload, loadMore, loadOnScroll } = usePosts()
</script>

<template>
  <main class="page posts-page bg-slate-50" aria-label="Publications" :aria-busy="isLoading">
    <div class="post-feed focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700" role="region" aria-label="Fil de publications" tabindex="0" @scroll.passive="loadOnScroll">
      <Post
        v-for="post in posts"
        :key="post.id"
        :title="post.title"
        :description="post.description"
        :user-id="post.userId"
        :image-url="post.imageUrl"
      />
      <div v-if="isLoading || error || !hasMore" class="feed-status p-6 text-center text-slate-600">
        <p v-if="isLoading" role="status">Chargement des publications…</p>
        <div v-else-if="error" role="alert">
          <p>{{ error }}</p>
          <button type="button" class="mt-3 min-h-11 cursor-pointer rounded-lg px-4 font-medium underline" @click="posts.length ? loadMore() : reload()">
            Réessayer
          </button>
        </div>
        <p v-else-if="!hasMore" role="status">Aucune publication pour le moment.</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.posts-page {
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px));
}

.post-feed {
  height: 100%;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  scroll-snap-type: y proximity;
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
