/**
 * services/api.js
 *
 * Centralised Axios instance.
 * All API calls go through here so auth headers and base URL
 * are applied in one place.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  // baseURL: 'http://34.44.46.97:8000/api/v1',
  timeout: 60_000 // 60 s — generous for AI calls
})

// Attach JWT on every request if present
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')

  if (token) {
    if (token.split('.').length === 3) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('[API] Request with valid token')
    } else {
      console.warn('[API] Invalid token format (not 3 segments)')
    }
  } else {
    console.log('[API] No token - anonymous request')
  }

  return config
})

// Handle responses and token refresh
let refreshPromise = null

api.interceptors.response.use(
  res => res,
  async err => {
    const originalRequest = err.config

    // Handle 401 Unauthorized
    if (err.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Prevent multiple simultaneous refresh attempts
      if (!refreshPromise) {
        refreshPromise = (async () => {
          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (!refreshToken) {
              throw new Error('No refresh token available')
            }

            console.log('[API] Attempting token refresh...')
            const res = await api.post('/auth/refresh', {
              refresh_token: refreshToken
            })

            const { access_token, refresh_token: newRefreshToken } = res.data
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('refresh_token', newRefreshToken)

            console.log('[API] ✓ Token refreshed')
            return access_token
          } catch (refreshErr) {
            console.error('[API] ✗ Token refresh failed:', refreshErr.message)
            // Clear auth and redirect to login
            localStorage.clear()
            window.location.href = '/auth'
            throw refreshErr
          } finally {
            refreshPromise = null
          }
        })()
      }

      try {
        const newToken = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshErr) {
        return Promise.reject(refreshErr)
      }
    }

    // Normalise error shape
    const msg =
      err.response?.data?.message ||
      err.response?.data?.detail ||
      err.message ||
      'An unknown error occurred'
    return Promise.reject(new Error(msg))
  }
)

export default api

// ── Typed service methods ─────────────────────────────────── //

/**
 * Upload a file and kick off the full ETL+AI pipeline.
 * @param {File}   file
 * @param {object} opts  { userObjective, tags, chatId }
 * @param {function} onProgress
 */
export async function analyzeFile(file, opts = {}, onProgress) {
  const form = new FormData()
  form.append('file', file)
  if (opts.userObjective) form.append('user_objective', opts.userObjective)
  if (opts.tags?.length)  form.append('tags', opts.tags.join(','))
  if (opts.chatId)        form.append('chat_id', opts.chatId)

  const res = await api.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    }
  })
  return res.data
}

/**
 * Generate an executive summary for a dashboard.
 * @param {string} dashboardId
 * @param {object} opts  { tags, userObjective, userStructure }
 */
export async function generateSummary(dashboardId, opts = {}) {
  const res = await api.post('/summary', {
    dashboard_id: dashboardId,
    tags: opts.tags || [],
    user_objective: opts.userObjective || null,
    user_structure: opts.userStructure || null
  })
  return res.data
}

/** Download PDF summary as a Blob */
export async function downloadSummaryPdf(dashboardId) {
  const res = await api.get(`/summary/${dashboardId}/pdf`, {
    responseType: 'blob'
  })
  return res.data
}

/**
 * Send a Q&A question to the mini-chat.
 * @param {string} dashboardId
 * @param {string} question
 * @param {Array}  history  [{ role, content }]
 */
export async function askQuestion(dashboardId, question, history = []) {
  const res = await api.post('/chat', {
    dashboard_id: dashboardId,
    question,
    history
  })
  return res.data
}

/** List all chat sessions for the authenticated user */
export async function listChats() {
  const res = await api.get('/chats')
  return res.data
}

/** Rename a chat session */
export async function renameChat(chatId, name) {
  const res = await api.patch(`/chats/${chatId}`, { name })
  return res.data
}

/** Delete a chat session and all its dashboards */
export async function deleteChat(chatId) {
  await api.delete(`/chats/${chatId}`)
}
