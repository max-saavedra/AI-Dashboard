import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/views/HomeView.vue'),
    name: 'home'
  },
  {
    // Main chat-style workspace — shows sidebar + chat area
    path: '/workspace',
    component: () => import('@/views/WorkspaceView.vue'),
    name: 'workspace'
  },
  {
    // Individual dashboard view (full-page)
    path: '/dashboard/:id',
    component: () => import('@/views/DashboardView.vue'),
    name: 'dashboard'
  },
  {
    path: '/auth',
    component: () => import('@/views/AuthView.vue'),
    name: 'auth'
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

export default router
