/**
 * stores/auth.js
 * Manages authentication state.
 * Uses localStorage for token persistence (Supabase JWT).
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const userId = ref(localStorage.getItem('user_id') || null)
  const email = ref(localStorage.getItem('user_email') || null)

  // Backward compat: also maintain token and user for existing code
  const token = computed(() => accessToken.value)
  const user = computed(() => ({
    id: userId.value,
    email: email.value
  }))

  const isAuthenticated = computed(() => !!accessToken.value && !!refreshToken.value)

  function isValidJWT(token) {
    return typeof token === 'string' && token.split('.').length === 3
  }

  function login(jwt, refreshJwt, uid, userEmail) {
    if (!isValidJWT(jwt)) {
      console.error('Invalid JWT received:', jwt)
      return
    }

    accessToken.value = jwt
    refreshToken.value = refreshJwt
    userId.value = uid
    email.value = userEmail

    localStorage.setItem('access_token', jwt)
    localStorage.setItem('refresh_token', refreshJwt)
    localStorage.setItem('user_id', uid)
    localStorage.setItem('user_email', userEmail)
  }

  function setAccessToken(jwt) {
    if (!isValidJWT(jwt)) {
      console.error('Invalid JWT received:', jwt)
      return
    }
    accessToken.value = jwt
    localStorage.setItem('access_token', jwt)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    userId.value = null
    email.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
  }

  return { token, user, isAuthenticated, login, logout, setAccessToken, accessToken, refreshToken }
})
