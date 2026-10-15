import { createRouter, createWebHistory } from 'vue-router'
import MapPage from '../pages/MapPage.vue'
import PostPage from '../pages/PostPage.vue'
import MessagesPage from '../pages/MessagesPage.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'map', component: MapPage, meta: { order: 0 } },
    { path: '/posts', name: 'posts', component: PostPage, meta: { order: 1 } },
    { path: '/messages', name: 'messages', component: MessagesPage, meta: { order: 2 } },
  ],
})
