import { onBeforeUnmount, onMounted, ref } from "vue";
import { POST_API_BASE_URL } from "../api/client";
import { getPosts } from "../api/posts";
import type { CommunityPost, PostItem } from "../types/post";

export function toPostItem(post: CommunityPost): PostItem {
  const images = (post.images ?? [])
    .slice()
    .sort((a, b) => (a.image_index ?? 0) - (b.image_index ?? 0))
    .map((img) => `${POST_API_BASE_URL}/images/${img.id}`);

  return {
    id: post.id,
    title: post.title,
    description: post.description,
    userId: post.user_id,
    hasLocation:
      post.latitude != null &&
      post.longitude != null &&
      Number.isFinite(post.latitude) &&
      Number.isFinite(post.longitude),
    latitude: post.latitude,
    longitude: post.longitude,
    startsAt: post.starts_at ?? undefined,
    endsAt: post.ends_at ?? undefined,
    imageUrl: images[0],
    images,
  };
}

export function usePosts() {
  const posts = ref<PostItem[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const hasMore = ref(true);
  let nextSkip = 0;
  const controller = new AbortController();

  async function loadPosts(reset = false) {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const result = await getPosts(
        reset ? 0 : nextSkip,
        20,
        controller.signal,
      );
      const items = result.posts.map(toPostItem);

      posts.value = reset ? items : [...posts.value, ...items];
      nextSkip = result.skip + result.posts.length;
      hasMore.value = result.posts.length === result.limit && result.limit > 0;
    } catch (cause) {
      if (!controller.signal.aborted) {
        error.value =
          cause instanceof Error
            ? cause.message
            : "Impossible de charger les publications.";
      }
    } finally {
      isLoading.value = false;
    }
  }

  function reload() {
    return loadPosts(true);
  }

  function loadMore() {
    if (hasMore.value) return loadPosts();
  }

  function loadOnScroll(event: Event) {
    if (error.value) return;

    const feed = event.currentTarget as HTMLElement;
    const distanceToBottom =
      feed.scrollHeight - feed.scrollTop - feed.clientHeight;
    if (distanceToBottom <= 200) void loadMore();
  }

  onMounted(reload);
  onBeforeUnmount(() => controller.abort());

  return { posts, isLoading, error, hasMore, reload, loadMore, loadOnScroll };
}
