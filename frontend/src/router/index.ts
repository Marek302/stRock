import { createRouter, createWebHistory } from 'vue-router'
import MapPage from '../pages/MapPage.vue'
import PostPage from '../pages/PostPage.vue'
import MessagesPage from '../pages/MessagesPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ProfilePage from '../pages/ProfilePage.vue'
import { auth, FirebaseService } from '../profile-auth/firebase'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'map', component: MapPage, meta: { order: 0 } },
    { path: '/posts', name: 'posts', component: PostPage, meta: { order: 1 } },
    { path: '/messages', name: 'messages', component: MessagesPage, meta: { order: 2 } },
    { path: '/login', name: 'login', component: LoginPage, meta: { order: 3 } },
    { path: '/profile', name: 'profile', component: ProfilePage, meta: { order: 3 } },
  ],
})

router.beforeEach(async (to) => {
  if (to.name !== 'login' && to.name !== 'profile') return

  await auth.authStateReady()

  if (to.name === 'profile' && !FirebaseService.currentUser) return { name: 'login' }
  if (to.name === 'login' && FirebaseService.currentUser) return { name: 'profile' }
})
