<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Button from "primevue/button";
import Carousel from "primevue/carousel";
import Galleria from "primevue/galleria";
import demoUsers from "../data/demo-users.json";

const props = defineProps<{
  postId: string;
  title: string;
  description: string;
  hasLocation: boolean;
  createdAt?: string;
  startsAt?: string;
  endsAt?: string;
  imageUrl?: string;
  contacting?: boolean;
  images?: string[];
  contactDisabled?: boolean;
  userId: string | number;
}>();

const demoAuthor = computed(() =>
  demoUsers.find((user) => user.uid === props.userId),
);

interface ImageDimension {
  width: number;
  height: number;
  ratio: number;
}

const imageList = computed(() => {
  if (props.images && props.images.length > 0) {
    return props.images.filter(Boolean);
  }
  if (props.imageUrl) {
    return [props.imageUrl];
  }
  return [];
});

const imageDimensions = ref<Record<string, ImageDimension>>({});

function registerImageDimension(url: string, width: number, height: number) {
  if (!url || width <= 0 || height <= 0) return;
  if (
    imageDimensions.value[url] &&
    imageDimensions.value[url].width === width &&
    imageDimensions.value[url].height === height
  ) {
    return;
  }
  imageDimensions.value = {
    ...imageDimensions.value,
    [url]: {
      width,
      height,
      ratio: width / height,
    },
  };
}

function onImageLoad(event: Event, url: string) {
  const target = event.target as HTMLImageElement | null;
  if (target?.naturalWidth && target?.naturalHeight) {
    registerImageDimension(url, target.naturalWidth, target.naturalHeight);
  }
}

watch(
  imageList,
  (urls) => {
    for (const url of urls) {
      if (imageDimensions.value[url]) continue;
      const img = new Image();
      img.src = url;
      if (img.complete && img.naturalWidth && img.naturalHeight) {
        registerImageDimension(url, img.naturalWidth, img.naturalHeight);
      } else {
        img.onload = () => {
          registerImageDimension(url, img.naturalWidth, img.naturalHeight);
        };
      }
    }
  },
  { immediate: true },
);

const carouselAspectRatio = computed(() => {
  const urls = imageList.value;
  const loaded = urls
    .map((url) => imageDimensions.value[url])
    .filter((dim): dim is ImageDimension =>
      Boolean(dim && dim.width > 0 && dim.height > 0),
    );

  if (loaded.length === 0) {
    return "16 / 9";
  }

  // Prioritize the image with the highest width (widest aspect ratio)
  let best = loaded[0];
  for (const dim of loaded) {
    if (dim.ratio > best.ratio) {
      best = dim;
    } else if (
      Math.abs(dim.ratio - best.ratio) < 0.01 &&
      dim.width > best.width
    ) {
      best = dim;
    }
  }

  return `${best.width} / ${best.height}`;
});

const isFullScreen = ref(false);
const activeImageIndex = ref(0);

function openFullScreen(index: number) {
  activeImageIndex.value = index;
  isFullScreen.value = true;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("fr-CA", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Toronto",
  }).format(new Date(value));
}

const emit = defineEmits<{
  contact: [userId: string | number];
  viewLocation: [postId: string];
}>();
</script>

<template>
  <article class="post" :aria-label="title">
    <h2 class="text-center text-2xl font-semibold text-slate-900">
      {{ title }}
    </h2>
    <div
      v-if="demoAuthor"
      class="mt-3 flex items-center justify-center gap-2 text-sm text-slate-500"
    >
      <img
        v-if="demoAuthor.photoURL"
        :src="demoAuthor.photoURL"
        alt=""
        class="h-9 w-9 shrink-0 rounded-full object-cover"
        loading="lazy"
      />
      <span>Par {{ demoAuthor.displayName }}</span>
    </div>
    <p v-if="createdAt" class="mt-2 text-center text-sm text-slate-500">
      Publié le <time :datetime="createdAt">{{ formatDate(createdAt) }}</time>
    </p>
    <p v-if="startsAt" class="mt-2 text-center text-sm text-slate-600">
      Événement : <time :datetime="startsAt">{{ formatDate(startsAt) }}</time>
      <template v-if="endsAt">
        — <time :datetime="endsAt">{{ formatDate(endsAt) }}</time></template
      >
    </p>
    <Carousel
      v-if="imageList.length > 0"
      :value="imageList"
      :num-visible="1"
      :num-scroll="1"
      :circular="imageList.length > 1"
      :show-navigators="imageList.length > 1"
      :show-indicators="imageList.length > 1"
      class="mt-6 w-full min-w-0"
    >
      <template #item="{ data, index }">
        <div
          class="group relative flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-lg bg-slate-100 max-h-[50dvh]"
          :style="{ aspectRatio: carouselAspectRatio }"
          role="button"
          tabindex="0"
          :aria-label="`Agrandir l'image ${index + 1} sur ${imageList.length} en plein écran`"
          @click="openFullScreen(index)"
          @keydown.enter.prevent="openFullScreen(index)"
          @keydown.space.prevent="openFullScreen(index)"
        >
          <img
            :src="data"
            :alt="
              imageList.length > 1
                ? `${title} (${index + 1}/${imageList.length})`
                : title
            "
            class="h-full w-full object-cover object-center transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
            decoding="async"
            @load="onImageLoad($event, data)"
          />
          <div
            class="pointer-events-none absolute bottom-3 right-3 flex items-center gap-1.5 rounded-full bg-slate-900/70 px-2.5 py-1 text-xs font-medium text-white shadow backdrop-blur-sm transition-opacity group-hover:bg-slate-900/90"
            aria-hidden="true"
          >
            <i class="pi pi-expand text-xs"></i>
            <span v-if="imageList.length > 1"
              >{{ index + 1 }} / {{ imageList.length }}</span
            >
            <span v-else>Plein écran</span>
          </div>
        </div>
      </template>
    </Carousel>

    <Galleria
      v-if="imageList.length > 0"
      v-model:visible="isFullScreen"
      v-model:activeIndex="activeImageIndex"
      :value="imageList"
      :circular="true"
      :full-screen="true"
      :show-item-navigators="imageList.length > 1"
      :show-thumbnails="imageList.length > 1"
      :show-indicators="false"
      class="fullscreen-galleria"
      container-class="fullscreen-galleria-container"
    >
      <template #closeicon>
        <button
          type="button"
          class="viewer-explicit-close-btn"
          aria-label="Fermer le plein écran"
          @click.stop="isFullScreen = false"
        >
          <i class="pi pi-times text-lg"></i>
        </button>
      </template>
      <template #item="{ item }">
        <div class="viewer-stage" @click="isFullScreen = false">
          <img :src="item" :alt="title" class="viewer-img" @click.stop />
        </div>
      </template>
      <template #thumbnail="{ item }">
        <img
          :src="item"
          :alt="title"
          class="h-14 w-20 rounded object-cover select-none"
        />
      </template>
    </Galleria>
    <p
      class="mt-6 whitespace-pre-line text-base leading-relaxed text-slate-600"
    >
      {{ description }}
    </p>
    <footer class="pt-6">
      <Button
        v-if="hasLocation"
        class="mb-3 min-h-11 w-full"
        label="Voir le lieu"
        severity="secondary"
        @click="emit('viewLocation', props.postId)"
      />
      <Button
        class="contact-author-button min-h-11 w-full"
        label="Contacter l’auteur"
        @click="emit('contact', props.userId)"
      />
    </footer>
  </article>
</template>

<style scoped>
.contact-author-button {
  --p-button-primary-background: #c05a20;
  --p-button-primary-border-color: #c05a20;
  --p-button-primary-color: #fff;
  --p-button-primary-hover-background: #a94e1b;
  --p-button-primary-hover-border-color: #a94e1b;
  --p-button-primary-hover-color: #fff;
  --p-button-primary-active-background: #914217;
  --p-button-primary-active-border-color: #914217;
  --p-button-primary-active-color: #fff;
  --p-button-primary-focus-ring-color: #c05a20;
}

.post {
  display: flex;
  flex-direction: column;
  width: 100%;
  margin-inline: auto;
  padding: 24px max(24px, env(safe-area-inset-right, 0px)) 24px
    max(24px, env(safe-area-inset-left, 0px));
  overflow-wrap: anywhere;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: white;
}

@media (min-width: 768px) {
  .post {
    max-width: 640px;
    padding: 32px;
  }
}
</style>

<style>
/* Full screen viewer container has a fixed consistent size covering the viewport */
.p-galleria-fullscreen.fullscreen-galleria-container {
  width: 100vw !important;
  height: 100dvh !important;
  max-width: 100vw !important;
  max-height: 100dvh !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: rgba(10, 15, 29, 0.96) !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
}

.fullscreen-galleria-container .p-galleria-content {
  flex: 1 1 0% !important;
  height: 100% !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
}

.fullscreen-galleria-container .p-galleria-items-container {
  flex: 1 1 0% !important;
  height: 100% !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  position: relative !important;
}

.fullscreen-galleria-container .p-galleria-items {
  flex: 1 1 0% !important;
  height: 100% !important;
  min-height: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  position: relative !important;
}

.fullscreen-galleria-container .p-galleria-item {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 !important;
}

/* Stage has consistent fixed dimensions so changing between wide/tall images doesn't shift the viewer */
.fullscreen-galleria-container .viewer-stage {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 24px max(24px, env(safe-area-inset-right, 0px)) 16px
    max(24px, env(safe-area-inset-left, 0px)) !important;
  box-sizing: border-box !important;
}

.fullscreen-galleria-container .viewer-img {
  max-width: 100% !important;
  max-height: 100% !important;
  width: auto !important;
  height: auto !important;
  object-fit: contain !important;
  user-select: none !important;
  -webkit-user-drag: none !important;
  border-radius: 8px !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
}

.fullscreen-galleria-container .p-galleria-thumbnails {
  flex-shrink: 0 !important;
  background: rgba(15, 23, 42, 0.8) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
  padding-bottom: env(safe-area-inset-bottom, 0px) !important;
}

/* Ensure the close button stays on top of everything and is fully clickable */
.fullscreen-galleria-container .p-galleria-close-button {
  position: absolute !important;
  top: max(16px, env(safe-area-inset-top, 0px)) !important;
  right: max(16px, env(safe-area-inset-right, 0px)) !important;
  z-index: 99999 !important;
  pointer-events: auto !important;
  cursor: pointer !important;
  width: 44px !important;
  height: 44px !important;
  border-radius: 50% !important;
  background: rgba(15, 23, 42, 0.75) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition:
    background 0.2s,
    transform 0.2s !important;
}

.fullscreen-galleria-container .p-galleria-close-button:hover {
  background: rgba(30, 41, 59, 0.95) !important;
  transform: scale(1.08) !important;
}

.viewer-explicit-close-btn {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: transparent !important;
  border: none !important;
  color: white !important;
  cursor: pointer !important;
  padding: 0 !important;
}
</style>
