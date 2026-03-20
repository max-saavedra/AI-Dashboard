// services/authService.js

import api from './api'
import { useAuthStore } from '@/stores/auth'

/**
 * Login with email and password
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token, refresh_token, user_id, email}>}
 */
export async function login(email, password) {
  const auth = useAuthStore()

  try {
    const res = await api.post('/auth/login', {
      email,
      password
    })

    const { access_token, refresh_token, user_id, email: userEmail } = res.data

    console.log('✓ LOGIN SUCCESS - Token received')
    console.log('TOKEN SEGMENTS:', access_token.split('.').length)

    // Save all tokens and user info
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user_id', user_id)
    localStorage.setItem('user_email', userEmail)

    // Update auth store
    auth.login(access_token, refresh_token, user_id, userEmail)

    return { access_token, refresh_token, user_id, email: userEmail }
  } catch (err) {
    console.error('✗ LOGIN FAILED:', err.message)
    throw err
  }
}

/**
 * Sign up with email and password
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token, refresh_token, user_id, email}>}
 */
export async function signup(email, password) {
  const auth = useAuthStore()

  try {
    const res = await api.post('/auth/signup', {
      email,
      password
    })

    const { access_token, refresh_token, user_id, email: userEmail } = res.data

    console.log('✓ SIGNUP SUCCESS - Account created')
    console.log('TOKEN SEGMENTS:', access_token.split('.').length)

    // Save all tokens and user info
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user_id', user_id)
    localStorage.setItem('user_email', userEmail)

    // Update auth store
    auth.login(access_token, refresh_token, user_id, userEmail)

    return { access_token, refresh_token, user_id, email: userEmail }
  } catch (err) {
    console.error('✗ SIGNUP FAILED:', err.message)
    throw err
  }
}

/**
 * Refresh access token using refresh token
 * @returns {Promise<boolean>}
 */
export async function refreshAccessToken() {
  try {
    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      console.warn('No refresh token available')
      return false
    }

    console.log('Attempting to refresh token...')

    const res = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    })

    const { access_token, refresh_token: newRefreshToken } = res.data

    // Update tokens
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', newRefreshToken)

    // Update auth store
    const auth = useAuthStore()
    auth.setAccessToken(access_token)

    console.log('✓ Token refreshed successfully')
    return true
  } catch (err) {
    console.error('✗ Token refresh failed:', err.message)
    // Clear auth on refresh failure
    logout()
    return false
  }
}

/**
 * Logout and clear auth state
 */
export function logout() {
  const auth = useAuthStore()
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_email')
  auth.logout()
  console.log('✓ Logged out')
}