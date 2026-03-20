<template>
  <div class="modal-backdrop" @click="maybeClose">
    <div class="summary-modal" @click.stop>
      <!-- Header -->
      <div class="summary-modal__head">
        <div class="head-left">
          <div class="head-icon">
            <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
            </svg>
          </div>
          <h2>Executive Summary</h2>
        </div>
        <button class="icon-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Content: show form if no summary yet, otherwise show summary -->
      <Transition name="fade" mode="out-in">
        <!-- Options form -->
        <div v-if="!store.summary && !store.phase.includes('summariz')" key="form" class="summary-form">
          <p class="form-intro">
            Neo will generate a professional executive summary from your dashboard data.
            Optionally customise the structure below.
          </p>

          <div class="form-field">
            <label class="form-label">Custom structure <span class="optional">(optional)</span></label>
            <textarea
              v-model="userStructure"
              class="form-textarea"
              rows="5"
              placeholder="e.g.&#10;1. Executive Overview&#10;2. Revenue Highlights&#10;3. Regional Performance&#10;4. Action Items"
            />
            <p class="field-hint">Leave blank to use Neo's default structure.</p>
          </div>

          <div class="form-field">
            <label class="form-label">Additional focus <span class="optional">(optional)</span></label>
            <input
              v-model="additionalObjective"
              class="form-input"
              placeholder="e.g. Focus on Q4 performance and year-over-year comparison"
            />
          </div>

          <div class="form-actions">
            <button class="btn btn--ghost" @click="$emit('close')">Cancel</button>
            <button class="btn btn--primary" @click="generateSummary">
              <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
              Generate Summary
            </button>
          </div>
        </div>

        <!-- Generating state -->
        <div v-else-if="store.phase === 'summarizing'" key="loading" class="summary-loading">
          <div class="loading-ring" aria-hidden="true">
            <div class="ring ring--outer" />
            <div class="ring ring--inner" />
            <span class="ring__letter">N</span>
          </div>
          <p class="loading-label">Generating your executive summary…</p>
          <p class="loading-hint">Analysing KPIs, trends, and patterns</p>
        </div>

        <!-- Summary display -->
        <div v-else-if="store.summary" key="summary" class="summary-display">
          <div class="summary-toolbar">
            <div class="toolbar-left">
              <span class="summary-label mono">Executive Summary</span>
              <span class="summary-date mono">{{ today }}</span>
            </div>
            <div class="toolbar-right">
              <button class="btn btn--ghost btn--sm" @click="regenerate">
                <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12">
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"/>
                </svg>
                Regenerate
              </button>
              <button class="btn btn--primary btn--sm" @click="downloadPdf" :disabled="downloading">
                <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12">
                  <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"/>
                </svg>
                {{ downloading ? 'Downloading…' : 'Download PDF' }}
              </button>
            </div>
          </div>

          <div class="summary-content">
            <div
              v-for="(paragraph, i) in formattedSummary"
              :key="i"
              class="summary-paragraph"
              :class="{
                'summary-paragraph--heading': paragraph.isHeading,
                'summary-paragraph--bullet': paragraph.isBullet
              }"
            >
              {{ paragraph.text }}
            </div>
          </div>
        </div>
      </Transition>

      <!-- Error display -->
      <div v-if="store.error" class="error-banner">
        {{ store.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const emit = defineEmits(['close'])
const store = useWorkspaceStore()

const userStructure       = ref('')
const additionalObjective = ref('')
const downloading         = ref(false)

const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })

// Parse raw summary text into typed paragraph objects for styled rendering
const formattedSummary = computed(() => {
  if (!store.summary) return []
  return store.summary
    .split('\n')
    .filter(line => line.trim())
    .map(line => {
      const trimmed = line.trim()
      // Detect numbered headings like "1. Executive Overview"
      const isHeading = /^\d+\.\s+[A-Z]/.test(trimmed) || /^#+\s/.test(trimmed)
      const isBullet  = trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')
      return {
        text: trimmed.replace(/^#+\s/, '').replace(/^[-•*]\s/, ''),
        isHeading,
        isBullet
      }
    })
})

async function generateSummary() {
  await store.requestSummary({
    userStructure:    userStructure.value || null,
    userObjective:    additionalObjective.value || store.userContext.objective || null
  })
}

function regenerate() {
  store.summary = ''
}

async function downloadPdf() {
  downloading.value = true
  try {
    await store.downloadPdf()
  } finally {
    downloading.value = false
  }
}

function maybeClose(e) {
  // Only close on backdrop click, not during generation
  if (store.phase !== 'summarizing') emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
  backdrop-filter: blur(6px);
  padding: 24px;
}

.summary-modal {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fadeIn 0.25s ease;
}

/* Header */
.summary-modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--col-border);
}
.head-left { display: flex; align-items: center; gap: 10px; }
.head-icon {
  width: 32px; height: 32px;
  background: rgba(37,99,235,0.15);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  color: var(--col-blue-400);
}
.summary-modal__head h2 { font-size: 1rem; font-weight: 600; }
.icon-btn {
  background: none; border: none; cursor: pointer;
  color: var(--col-text-dim); font-size: 1rem;
  padding: 4px 8px; border-radius: 4px;
  transition: color var(--t-fast);
}
.icon-btn:hover { color: var(--col-text-primary); }

/* Form */
.summary-form {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}
.form-intro { font-size: 0.88rem; color: var(--col-text-secondary); line-height: 1.6; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-size: 0.8rem; font-weight: 500; color: var(--col-text-secondary);
}
.optional { color: var(--col-text-dim); font-weight: 400; font-size: 0.75rem; }
.form-textarea, .form-input {
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.88rem;
  padding: 10px 12px;
  transition: border-color var(--t-fast);
  resize: vertical;
}
.form-textarea:focus, .form-input:focus {
  outline: none; border-color: var(--col-blue-600);
}
.form-textarea::placeholder, .form-input::placeholder { color: var(--col-text-dim); }
.field-hint { font-size: 0.75rem; color: var(--col-text-dim); }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; }

/* Loading */
.summary-loading {
  padding: 60px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.loading-ring {
  position: relative;
  width: 72px; height: 72px;
  display: flex; align-items: center; justify-content: center;
}
.ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid transparent;
}
.ring--outer {
  inset: 0;
  border-color: rgba(37,99,235,0.6);
  animation: spin 2s linear infinite;
}
.ring--inner {
  inset: 12px;
  border-color: rgba(37,99,235,0.25);
  animation: spin 1.5s linear infinite reverse;
}
.ring__letter {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1.1rem;
  background: linear-gradient(135deg, #60A5FA, #2563EB);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  z-index: 1;
}
.loading-label { font-size: 1rem; font-weight: 600; color: var(--col-text-primary); }
.loading-hint  { font-size: 0.83rem; color: var(--col-text-dim); font-family: var(--font-mono); }

/* Summary display */
.summary-display {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}
.summary-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--col-border);
  background: var(--col-surface);
  flex-wrap: wrap;
  gap: 10px;
}
.toolbar-left  { display: flex; align-items: center; gap: 12px; }
.toolbar-right { display: flex; align-items: center; gap: 8px; }
.summary-label { font-size: 0.75rem; color: var(--col-blue-400); text-transform: uppercase; letter-spacing: 0.08em; }
.summary-date  { font-size: 0.72rem; color: var(--col-text-dim); }

.summary-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.summary-paragraph {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--col-text-secondary);
}
.summary-paragraph--heading {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--col-text-primary);
  margin-top: 12px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--col-border);
}
.summary-paragraph--bullet {
  padding-left: 16px;
  position: relative;
}
.summary-paragraph--bullet::before {
  content: '·';
  position: absolute;
  left: 4px;
  color: var(--col-blue-400);
  font-weight: 700;
}

/* Error */
.error-banner {
  padding: 12px 24px;
  background: rgba(239,68,68,0.08);
  border-top: 1px solid rgba(239,68,68,0.2);
  color: var(--col-error);
  font-size: 0.83rem;
}

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 6px; border-radius: var(--radius-md); font-size: 0.88rem; font-weight: 500; font-family: var(--font-body); cursor: pointer; border: none; transition: all var(--t-fast); }
.btn--sm { padding: 7px 12px; font-size: 0.82rem; }
.btn--ghost { background: transparent; color: var(--col-text-secondary); border: 1px solid var(--col-border); }
.btn--ghost:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }
.btn--primary { background: var(--col-blue-600); color: white; }
.btn--primary:hover { background: var(--col-blue-700); }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.mono { font-family: var(--font-mono); }
</style>
