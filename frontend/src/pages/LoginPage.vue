<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { FirebaseService } from '../profile-auth/firebase';

const router = useRouter();
const isLoading = ref(false);
const errorMsg = ref('');

async function signInWithGoogle() {
  if (isLoading.value) return;
  isLoading.value = true;
  errorMsg.value = '';
  try {
    await FirebaseService.signInWithGoogle();
    await router.replace({ name: 'profile' });
  } catch (error) {
    const message = error instanceof Error ? error.message : '';
    errorMsg.value = message.includes('popup') || message.includes('closed')
      ? 'Sign-in popup was closed or blocked. You can retry.'
      : 'Sign in failed. Please try again.';
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <main class="page auth-page bg-slate-50 flex items-center justify-center" aria-label="Connexion">
    <div class="bg-white max-w-sm w-full rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
      <!-- roch-on Brand Header -->
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center w-12 h-12 bg-slate-900 text-white rounded-2xl font-black text-xl mb-3 shadow-sm tracking-tighter">
          R
        </div>
        <div class="flex items-center justify-center gap-1.5">
          <h1 class="text-2xl font-black tracking-tight text-slate-900">roch-on</h1>
          <span class="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
            Google Auth
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Sign in to access your profile
        </p>
      </div>

      <!-- Error notice -->
      <div v-if="errorMsg" role="alert" class="mb-4 p-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl">
        {{ errorMsg }}
      </div>

      <!-- Google Sign In Button Only -->
      <button
        type="button"
        :disabled="isLoading"
        @click="signInWithGoogle"
        class="w-full flex items-center justify-center gap-3 py-3 px-4 border border-slate-300 rounded-xl text-sm font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-2xs disabled:opacity-50"
      >
        <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span>{{ isLoading ? 'Connecting to Google...' : 'Continue with Google' }}</span>
      </button>
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