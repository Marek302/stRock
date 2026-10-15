<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { FirebaseService, type UserProfile } from '../profile-auth/firebase';
import { Camera, Check, LogOut } from 'lucide-vue-next';

const router = useRouter();
const user = FirebaseService.currentUser;
const profile = ref<UserProfile>({
  uid: user?.uid || '',
  email: user?.email || '',
  displayName: user?.displayName || '',
  photoURL: user?.photoURL || '',
});
const errorMsg = ref('');
const isSaving = ref(false);

onMounted(async () => {
  if (!user) return;
  try {
    const savedProfile = await FirebaseService.getProfile(user.uid);
    if (savedProfile) profile.value = savedProfile;
  } catch {
    errorMsg.value = 'Impossible de charger le profil.';
  }
});

const fileInputRef = ref<HTMLInputElement | null>(null);
const savedNotice = ref(false);

const handlePhotoUpload = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    const rawDataUrl = event.target?.result as string;
    const img = new Image();
    img.onload = () => {
      const maxDim = 256;
      let width = img.width;
      let height = img.height;

      if (width > height) {
        if (width > maxDim) {
          height = Math.round((height * maxDim) / width);
          width = maxDim;
        }
      } else {
        if (height > maxDim) {
          width = Math.round((width * maxDim) / height);
          height = maxDim;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(img, 0, 0, width, height);
        const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.85);
        profile.value.photoURL = compressedDataUrl;
      } else {
        profile.value.photoURL = rawDataUrl;
      }
    };
    img.src = rawDataUrl;
  };
  reader.readAsDataURL(file);
  target.value = '';
};

const handleSave = async () => {
  if (isSaving.value) return;
  isSaving.value = true;
  savedNotice.value = false;
  errorMsg.value = '';
  try {
    await FirebaseService.saveProfile(profile.value);
    savedNotice.value = true;
  } catch {
    errorMsg.value = 'Impossible d’enregistrer le profil.';
  } finally {
    isSaving.value = false;
  }
};

const handleLogout = async () => {
  errorMsg.value = '';
  try {
    await FirebaseService.signOut();
    await router.replace({ name: 'login' });
  } catch {
    errorMsg.value = 'Impossible de se déconnecter.';
  }
};
</script>

<template>
  <main class="page auth-page bg-slate-50 flex flex-col justify-between" aria-label="Profil">
    <div class="max-w-sm w-full mx-auto my-auto py-4 sm:py-6">
      <!-- Top Bar: roch-on branding & Log Out -->
      <div class="flex items-center justify-between mb-5">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 bg-slate-900 text-white rounded-lg flex items-center justify-center font-black text-xs shadow-2xs">
            R
          </div>
          <span class="font-bold text-slate-900 text-sm tracking-tight">roch-on</span>
        </div>

        <button
          type="button"
          @click="handleLogout"
          class="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-rose-600 transition-colors py-1 px-2.5 rounded-lg hover:bg-slate-100"
        >
          <LogOut class="w-3.5 h-3.5" />
          <span>Log Out</span>
        </button>
      </div>

      <p v-if="errorMsg" role="alert" class="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{{ errorMsg }}</p>

      <!-- Main Profile Card -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <!-- Avatar Picture & Upload Controls -->
        <div class="flex flex-col items-center text-center">
          <div class="relative">
            <div class="w-24 h-24 rounded-full bg-slate-100 border-2 border-slate-200 overflow-hidden shadow-xs flex items-center justify-center">
              <img
                v-if="profile.photoURL"
                :src="profile.photoURL"
                :alt="profile.displayName"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-3xl font-bold text-slate-400">
                {{ profile.displayName?.charAt(0) || user?.displayName?.charAt(0) || 'U' }}
              </span>
            </div>

            <!-- Camera button overlay -->
            <button
              type="button"
              @click="fileInputRef?.click()"
              class="absolute bottom-0 right-0 p-2 bg-slate-900 text-white rounded-full shadow-md hover:bg-slate-800 transition-colors"
              title="Change Photo"
              aria-label="Upload photo"
            >
              <Camera class="w-3.5 h-3.5" />
            </button>
          </div>

          <input
            type="file"
            ref="fileInputRef"
            accept="image/*"
            @change="handlePhotoUpload"
            class="hidden"
          />

          <!-- Action links -->
          <div class="flex items-center gap-2.5 mt-3">
            <button
              type="button"
              @click="fileInputRef?.click()"
              class="text-xs font-semibold text-slate-900 hover:underline"
            >
              Upload Photo
            </button>
            <template v-if="profile.photoURL">
              <span class="text-slate-300">·</span>
              <button
                type="button"
                @click="profile.photoURL = ''"
                class="text-xs text-rose-600 hover:underline"
              >
                Remove
              </button>
            </template>
          </div>
        </div>

        <!-- Inputs -->
        <div class="space-y-4 pt-1">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Display Name
            </label>
            <input
              type="text"
              v-model="profile.displayName"
              placeholder="Your Name"
              class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-900"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">
              Email
            </label>
            <input
              type="email"
              disabled
              :value="profile.email"
              class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed"
            />
          </div>
        </div>

        <!-- Save Button -->
        <div class="pt-2">
          <button
            type="button"
            @click="handleSave"
            :disabled="isSaving"
            class="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center gap-2 shadow-2xs"
          >
            <template v-if="savedNotice">
              <Check class="w-4 h-4 text-emerald-400" />
              <span>Saved to roch-on!</span>
            </template>
            <template v-else>
              <span>Save Profile</span>
            </template>
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.auth-page {
  overflow-y: auto;
  padding: 112px 16px calc(var(--mobile-navbar-height) + env(safe-area-inset-bottom, 0px) + 24px);
}

@media (min-width: 768px) {
  .auth-page {
    padding-bottom: 24px;
  }
}
</style>
