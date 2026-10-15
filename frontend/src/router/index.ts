import { createRouter, createWebHistory } from 'vue-router'
import MapPage from '../pages/MapPage.vue'
import PostPage from '../pages/PostPage.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'map', component: MapPage },
    { path: '/posts', name: 'posts', component: PostPage },
  ],
})
