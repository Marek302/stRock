<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { FirebaseService, type UserProfile } from '../profile-auth/firebase';
import { LogOut } from 'lucide-vue-next';

const router = useRouter();
const user = FirebaseService.currentUser;
const profile = ref<UserProfile>({
  uid: user?.uid || '',
  email: user?.email || '',
  displayName: user?.displayName || '',
  photoURL: user?.photoURL || '',
});
const errorMsg = ref('');

onMounted(async () => {
  if (!user) return;
  try {
    const savedProfile = await FirebaseService.getProfile(user.uid);
    if (savedProfile) {
      profile.value = savedProfile;
    }
  } catch {
    // Les informations du compte connecté restent disponibles si Firestore échoue.
  }
});

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

      <p v-if="errorMsg" role="alert" class="mb-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">
        {{ errorMsg }}
      </p>

      <!-- Main Profile Card (Read-only View) -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <!-- Avatar Picture (Read-only) -->
        <div class="flex flex-col items-center text-center">
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

          <h2 class="text-base font-bold text-slate-900 mt-3">
            {{ profile.displayName || user?.displayName || 'User' }}
          </h2>
          <p class="text-xs text-slate-500">
            {{ profile.email || user?.email }}
          </p>
        </div>

        <!-- Details (Read-only) -->
        <div class="space-y-3 pt-2 border-t border-slate-100">
          <div>
            <span class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Display Name
            </span>
            <div class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-medium">
              {{ profile.displayName || user?.displayName || 'Not set' }}
            </div>
          </div>

          <div>
            <span class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Email Address
            </span>
            <div class="w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-medium">
              {{ profile.email || user?.email }}
            </div>
          </div>
        </div>

        <!-- Log Out Action Button -->
        <div class="pt-2">
          <button
            type="button"
            @click="handleLogout"
            class="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl text-xs sm:text-sm transition-colors flex items-center justify-center gap-2"
          >
            <LogOut class="w-4 h-4 text-slate-500" />
            <span>Sign Out</span>
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
