<script setup lang="ts">
import Post from '../components/Post.vue'

const posts = [
  {
    id: 'demo-1',
    title: 'Une balade dans Saint-Roch',
    description: 'Envie de découvrir le quartier à pied ? Je propose une balade pour explorer les petites rues et partager nos endroits préférés. Tout le monde est bienvenu !',
    userId: 'user-1',
  },
  {
    id: 'demo-2',
    title: 'Un café entre voisins',
    description: 'Je viens de m’installer dans Saint-Roch et j’aimerais rencontrer du monde autour d’un café. Si ça te tente, contacte-moi pour qu’on organise ça.',
    userId: 'user-2',
  },
  {
    id: 'demo-3',
    title: 'Des livres à partager',
    description: 'J’ai quelques romans à échanger. Une belle occasion de découvrir de nouvelles lectures et de discuter avec les gens du quartier.',
    userId: 'user-3',
  },
]
</script>

<template>
  <main class="page posts-page bg-slate-50" aria-label="Publications">
    <div class="post-feed focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700" role="region" aria-label="Fil de publications" tabindex="0">
      <Post
        v-for="post in posts"
        :key="post.id"
        :title="post.title"
        :description="post.description"
        :user-id="post.userId"
      />
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

@media (min-width: 768px) {
  .posts-page {
    padding-top: 112px;
    padding-bottom: 0;
  }
}
</style>
