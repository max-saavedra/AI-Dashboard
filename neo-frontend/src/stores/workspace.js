/**
 * stores/workspace.js
 *
 * Central state for the chat-style workspace.
 * Manages: sessions list, active session, dashboard results,
 * upload wizard state, summary, and Q&A history.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  analyzeFile,
  listChats,
  deleteChat,
  renameChat,
  generateSummary,
  downloadSummaryPdf,
  askQuestion
} from '@/services/api'

export const useWorkspaceStore = defineStore('workspace', () => {
  // ── Sessions (sidebar) ─────────────────────────────────── //
  const sessions    = ref([])   // [{ chat_id, name, created_at, dashboard_count }]
  const activeId    = ref(null) // active chat_id

  // ── Current analysis result ────────────────────────────── //
  const result      = ref(null) // full AnalysisResult from backend
  const summary     = ref('')   // executive summary text

  // ── UI state ───────────────────────────────────────────── //
  const phase       = ref('idle') // idle | uploading | processing | dashboard | summarizing
  const uploadPct   = ref(0)
  const error       = ref(null)

  // ── Q&A history per dashboard ──────────────────────────── //
  const qaHistory   = ref([]) // [{ role: 'user'|'assistant', content }]

  // ── Wizard user context ────────────────────────────────── //
  const userContext = ref({
    role: '',
    objective: '',
    tags: []
  })

  // ── Active charts selection (which charts user shows) ──── //
  const visibleCharts = ref([]) // ids of visible charts

  // ── Filters applied by the user ───────────────────────── //
  const activeFilters = ref({}) // { columnName: value }

  // ─────────────────────────────────────────────────────────
  const isProcessing = computed(() =>
    ['uploading', 'processing'].includes(phase.value)
  )

  const hasDashboard = computed(() => result.value !== null)

  const currentCharts = computed(() => {
    if (!result.value) return []
    const configs = result.value.chart_configs || []
    if (visibleCharts.value.length === 0) return configs.slice(0, 3)
    return configs.filter(c => visibleCharts.value.includes(c.id))
  })

  // ── Actions ───────────────────────────────────────────── //

  async function fetchSessions() {
    try {
      sessions.value = await listChats()
    } catch {
      // Anonymous user — no sessions available
      sessions.value = []
    }
  }

  async function runAnalysis(file, chatId = null) {
    phase.value   = 'uploading'
    uploadPct.value = 0
    error.value   = null
    result.value  = null
    summary.value = ''
    qaHistory.value = []

    try {
      const data = await analyzeFile(
        file,
        {
          userObjective: userContext.value.objective,
          tags:          userContext.value.tags,
          chatId
        },
        pct => {
          uploadPct.value = pct
          if (pct === 100) phase.value = 'processing'
        }
      )

      result.value = data
      phase.value  = 'dashboard'

      // Default: show first 3 charts
      visibleCharts.value = (data.chart_configs || [])
        .slice(0, 3)
        .map(c => c.id)

      // Refresh session list (new chat may have been created)
      await fetchSessions()

      if (data.chat_id) activeId.value = data.chat_id

    } catch (err) {
      error.value  = err.message
      phase.value  = 'idle'
    }
  }

  async function requestSummary(opts = {}) {
    if (!result.value) return
    phase.value = 'summarizing'
    error.value = null
    try {
      const res = await generateSummary(result.value.dashboard_id, {
        tags:          userContext.value.tags,
        userObjective: userContext.value.objective,
        ...opts
      })
      summary.value = res.summary
    } catch (err) {
      error.value = err.message
    } finally {
      phase.value = 'dashboard'
    }
  }

  async function downloadPdf() {
    if (!result.value) return
    const blob = await downloadSummaryPdf(result.value.dashboard_id)
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = 'neo-executive-summary.pdf'
    a.click()
    URL.revokeObjectURL(url)
  }

  async function sendQuestion(question) {
    if (!result.value) return
    const userMsg = { role: 'user', content: question }
    qaHistory.value.push(userMsg)

    try {
      const res = await askQuestion(
        result.value.dashboard_id,
        question,
        qaHistory.value.slice(-10)
      )
      qaHistory.value.push({ role: 'assistant', content: res.answer })
    } catch (err) {
      qaHistory.value.push({
        role: 'assistant',
        content: 'I could not process that question. Please try again.'
      })
    }
  }

  async function removeSession(chatId) {
    await deleteChat(chatId)
    sessions.value = sessions.value.filter(s => s.chat_id !== chatId)
    if (activeId.value === chatId) {
      activeId.value = null
      result.value   = null
      phase.value    = 'idle'
    }
  }

  async function renameSession(chatId, name) {
    await renameChat(chatId, name)
    const s = sessions.value.find(s => s.chat_id === chatId)
    if (s) s.name = name
  }

  function resetToIdle() {
    phase.value     = 'idle'
    result.value    = null
    summary.value   = ''
    qaHistory.value = []
    error.value     = null
    visibleCharts.value = []
    activeFilters.value = {}
  }

  function toggleChart(chartId) {
    const idx = visibleCharts.value.indexOf(chartId)
    if (idx === -1) visibleCharts.value.push(chartId)
    else            visibleCharts.value.splice(idx, 1)
  }

  function setFilter(column, value) {
    if (value === null || value === '') {
      const f = { ...activeFilters.value }
      delete f[column]
      activeFilters.value = f
    } else {
      activeFilters.value = { ...activeFilters.value, [column]: value }
    }
  }

  return {
    sessions, activeId, result, summary, phase,
    uploadPct, error, userContext, qaHistory,
    visibleCharts, activeFilters,
    isProcessing, hasDashboard, currentCharts,
    fetchSessions, runAnalysis, requestSummary,
    downloadPdf, sendQuestion, removeSession,
    renameSession, resetToIdle, toggleChart, setFilter
  }
})
