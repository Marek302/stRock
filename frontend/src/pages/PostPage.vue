<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { getPost } from "../api/posts";
import type { CommunityPost, PostItem } from "../types/post";
import Post from "../components/Post.vue";
import CreatePostButton from "../components/CreatePostButton.vue";
import PostCreationOverlay from "../components/PostCreationOverlay.vue";
import { toPostItem, usePosts } from "../composables/usePosts";
import { MessagingApi } from "../api/messagingApi";
import {
  clearPostCreationDraft,
  selectPostLocation,
} from "../composables/usePostCreation";

const { posts, isLoading, error, hasMore, reload, loadMore, loadOnScroll } =
  usePosts();
const route = useRoute();
const router = useRouter();
const contactingPostId = ref<string | null>(null);
const contactError = ref("");
const selectedPost = ref<PostItem | null>(null);
const selectedLoading = ref(false);
const selectedError = ref<string | null>(null);
const feedElement = ref<HTMLElement | null>(null);
const isCreationOpen = ref(false);
let previousFocus: HTMLElement | null = null;
const displayedPosts = computed(() =>
  selectedPost.value
    ? [
        selectedPost.value,
        ...posts.value.filter((post) => post.id !== selectedPost.value?.id),
      ]
    : posts.value,
);

function openCreation() {
  previousFocus =
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
  isCreationOpen.value = true;
}

async function closeCreation() {
  isCreationOpen.value = false;
  clearPostCreationDraft();
  await nextTick();
  previousFocus?.focus();
}

async function selectLocation() {
  isCreationOpen.value = false;
  await router.push({ name: "map", query: { pickPostLocation: "1" } });
}

function showPostLocation(post: PostItem) {
  if (post.latitude == null || post.longitude == null) return;
  void router.push({
    name: "map",
    query: {
      post: post.id,
      latitude: String(post.latitude),
      longitude: String(post.longitude),
    },
  });
}

async function handleCreated(post: CommunityPost) {
  await closeCreation();
  if (post.content_type === 'safety_alert') {
    await router.replace({ name: 'map', query: { post: post.id } });
  } else {
    await router.replace({ name: "posts", query: { post: post.id } });
  }
  void reload();
}

watch(
  () => route.name,
  (name) => {
    if (name !== "posts") isCreationOpen.value = false;
  },
);

watch(
  () => route.query.resumePost,
  (resume) => {
    if (route.name !== "posts" || resume !== "1") return;
    const latitude = Number(route.query.latitude);
    const longitude = Number(route.query.longitude);
    if (
      typeof route.query.latitude === "string" &&
      typeof route.query.longitude === "string" &&
      Number.isFinite(latitude) &&
      Number.isFinite(longitude) &&
      Math.abs(latitude) <= 90 &&
      Math.abs(longitude) <= 180
    ) {
      void selectPostLocation(latitude, longitude);
    }
    isCreationOpen.value = true;
    void router.replace({
      name: "posts",
      query: {
        ...route.query,
        resumePost: undefined,
        latitude: undefined,
        longitude: undefined,
      },
    });
  },
  { immediate: true },
);

watch(
  () => (route.name === "posts" ? route.query.post : undefined),
  async (id, _previous, onCleanup) => {
    selectedPost.value = null;
    selectedError.value = null;
    selectedLoading.value = false;
    if (typeof id !== "string" || !id) return;
    const controller = new AbortController();
    onCleanup(() => controller.abort());
    selectedLoading.value = true;
    try {
      const loadedPost = await getPost(id, controller.signal);
      if (loadedPost.content_type === 'safety_alert') {
        await router.replace({ name: 'map', query: { post: loadedPost.id } });
        return;
      }
      selectedPost.value = toPostItem(loadedPost);
      await nextTick();
      feedElement.value?.scrollTo({ top: 0 });
      feedElement.value
        ?.querySelector<HTMLElement>('[data-selected="true"]')
        ?.focus({ preventScroll: true });
    } catch (cause) {
      if (!controller.signal.aborted) {
        selectedError.value =
          cause instanceof Error
            ? cause.message
            : "Impossible de charger la publication.";
      }
    } finally {
      if (!controller.signal.aborted) selectedLoading.value = false;
    }
  },
  { immediate: true },
);

async function contactAuthor(postId: string, userId: string | number) {
  if (contactingPostId.value) return;
  contactingPostId.value = postId;
  contactError.value = "";
  try {
    const conversation = await MessagingApi.createConversation(postId);
    if (!conversation.participants.includes(String(userId))) {
      throw new Error(
        "La discussion ne correspond pas à l’auteur de cette publication.",
      );
    }
    await router.push({
      name: "messages",
      query: { conversation: conversation.id, user: String(userId) },
    });
  } catch (err) {
    contactError.value =
      err instanceof Error ? err.message : "Impossible de contacter l’auteur.";
  } finally {
    contactingPostId.value = null;
  }
}
</script>

<template>
  <main
    class="page posts-page bg-slate-50"
    aria-label="Publications"
    :aria-busy="isLoading || selectedLoading"
  >
    <div
      ref="feedElement"
      class="post-feed focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-sky-700"
      role="region"
      aria-label="Fil de publications"
      tabindex="0"
      @scroll.passive="loadOnScroll"
    >
      <p
        v-if="selectedLoading"
        class="p-6 text-center text-slate-600"
        role="status"
      >
        Chargement de la publication…
      </p>
      <div
        v-if="selectedError"
        class="p-6 text-center text-red-700"
        role="alert"
      >
        <p>{{ selectedError }}</p>
        <RouterLink
          :to="{ name: 'posts' }"
          class="mt-3 inline-block min-h-11 underline"
          >Voir toutes les publications</RouterLink
        >
      </div>
      <p v-if="contactError" role="alert" class="p-4 text-center text-red-700">
        {{ contactError }}
      </p>
      <Post
        v-for="post in displayedPosts"
        :key="post.id"
        :data-selected="post.id === selectedPost?.id"
        :class="{ 'selected-post': post.id === selectedPost?.id }"
        tabindex="-1"
        :title="post.title"
        :post-id="post.id"
        :description="post.description"
        :user-id="post.userId"
        :image-url="post.imageUrl"
        :has-location="post.hasLocation"
        :images="post.images"
        :location="post.location"
        :created-at="post.createdAt"
        :starts-at="post.startsAt"
        :ends-at="post.endsAt"
        :contacting="contactingPostId === post.id"
        :contact-disabled="contactingPostId !== null"
        @contact="contactAuthor(post.id, $event)"
        @view-location="showPostLocation(post)"
      />
      <div
        v-if="isLoading || error || !hasMore"
        class="feed-status p-6 text-center text-slate-600"
      >
        <p v-if="isLoading" role="status">Chargement des publications…</p>
        <div v-else-if="error" role="alert">
          <p>{{ error }}</p>
          <button
            type="button"
            class="mt-3 min-h-11 cursor-pointer rounded-lg px-4 font-medium underline"
            @click="posts.length ? loadMore() : reload()"
          >
            Réessayer
          </button>
        </div>
        <p v-else-if="!displayedPosts.length" role="status">
          Aucune publication pour le moment.
        </p>
      </div>
    </div>
    <CreatePostButton @click="openCreation" />
    <Teleport to="body">
      <PostCreationOverlay
        v-if="isCreationOpen"
        @close="closeCreation"
        @created="handleCreated"
        @select-location="selectLocation"
      />
    </Teleport>
  </main>
</template>

<style scoped>
.posts-page {
  padding-top: calc(72px + env(safe-area-inset-top, 0px));
  padding-bottom: calc(
    var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px)
  );
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
