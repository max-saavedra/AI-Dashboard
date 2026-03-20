<template>
  <div class="wizard">
    <!-- Welcome message -->
    <div class="wizard__welcome">
      <div class="welcome-icon">
        <span>✦</span>
      </div>
      <h2 class="welcome-title">What would you like to analyse?</h2>
      <p class="welcome-sub">
        Upload an Excel or CSV file and Neo will generate an interactive dashboard
        powered by AI — instantly.
      </p>
    </div>

    <!-- Step 1: Drop zone -->
    <div v-if="step === 1" class="wizard__card anim-fade-in">
      <div
        class="drop-zone"
        :class="{
          'drop-zone--over': isDragging,
          'drop-zone--selected': selectedFile
        }"
        @dragenter.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="$refs.fileInput.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.csv"
          class="sr-only"
          @change="handleFileChange"
        />

        <div v-if="!selectedFile" class="drop-zone__empty">
          <div class="drop-icon">
            <svg viewBox="0 0 48 48" fill="none" width="48" height="48">
              <rect x="4" y="8" width="40" height="32" rx="4" stroke="currentColor" stroke-width="2"/>
              <path d="M16 28l8-8 8 8M24 20v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <p class="drop-zone__label">Drop your file here</p>
          <p class="drop-zone__hint">or click to browse · Excel (.xlsx) or CSV</p>
          <p class="drop-zone__limit">Maximum 10 MB</p>
        </div>

        <div v-else class="drop-zone__selected">
          <div class="file-icon">{{ fileIcon }}</div>
          <div class="file-info">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
          </div>
          <button class="clear-btn" @click.stop="clearFile" title="Remove">✕</button>
        </div>
      </div>

      <div v-if="fileError" class="error-msg">{{ fileError }}</div>

      <button
        class="btn btn--primary btn--full"
        :disabled="!selectedFile"
        @click="step = 2"
      >
        Continue
        <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
          <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"/>
        </svg>
      </button>
    </div>

    <!-- Step 2: Context form -->
    <div v-else-if="step === 2" class="wizard__card anim-fade-in">
      <div class="step-header">
        <button class="back-btn" @click="step = 1">← Back</button>
        <span class="step-file">{{ selectedFile?.name }}</span>
      </div>

      <h3 class="step-title">Tell Neo about yourself</h3>
      <p class="step-hint">This helps personalise your dashboard. All fields are optional.</p>

      <div class="form-grid">
        <div class="form-field">
          <label class="form-label">Your role</label>
          <select class="form-select" v-model="context.role">
            <option value="">Select a role…</option>
            <option v-for="r in roles" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>

        <div class="form-field">
          <label class="form-label">Analysis objective</label>
          <textarea
            class="form-textarea"
            v-model="context.objective"
            placeholder="e.g. Understand which products drive the most revenue in Q4…"
            rows="3"
          />
        </div>

        <div class="form-field">
          <label class="form-label">Focus tags</label>
          <div class="tags-input">
            <div class="tags-list">
              <span v-for="tag in context.tags" :key="tag" class="tag">
                {{ tag }}
                <button @click="removeTag(tag)">✕</button>
              </span>
            </div>
            <input
              class="tag-input"
              v-model="tagInput"
              placeholder="Add a tag and press Enter"
              @keydown.enter.prevent="addTag"
              @keydown.comma.prevent="addTag"
            />
          </div>
          <p class="field-hint">e.g. sales, revenue, Q4, performance</p>
        </div>
      </div>

      <button
        class="btn btn--primary btn--full"
        @click="submitWizard"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
        Generate Dashboard
      </button>
    </div>

    <!-- Suggested analyses -->
    <div class="wizard__suggestions">
      <p class="suggestions-label">Try with a sample</p>
      <div class="suggestions-grid">
        <button
          v-for="s in suggestions"
          :key="s.label"
          class="suggestion-chip"
          @click="applySuggestion(s)"
        >
          <span>{{ s.icon }}</span>
          {{ s.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['submit'])

const step         = ref(1)
const selectedFile = ref(null)
const isDragging   = ref(false)
const fileError    = ref('')
const tagInput     = ref('')

const context = ref({
  role:      '',
  objective: '',
  tags:      []
})

const roles = [
  'CEO / Executive', 'Sales Manager', 'Marketing Manager',
  'Data Analyst', 'Financial Analyst', 'Operations Manager',
  'Product Manager', 'HR Manager', 'Consultant', 'Other'
]

const suggestions = [
  { icon: '📈', label: 'Sales performance', objective: 'Analyse sales trends and identify top-performing products', tags: ['sales', 'revenue'] },
  { icon: '💰', label: 'Financial overview', objective: 'Understand key financial metrics and cash flow trends', tags: ['finance', 'costs'] },
  { icon: '👥', label: 'HR analytics',  objective: 'Understand workforce composition and turnover patterns', tags: ['hr', 'headcount'] }
]

const fileIcon = computed(() => {
  if (!selectedFile.value) return '📄'
  return selectedFile.value.name.endsWith('.csv') ? '📋' : '📊'
})

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) validateAndSet(file)
}

function handleFileChange(e) {
  const file = e.target.files[0]
  if (file) validateAndSet(file)
}

function validateAndSet(file) {
  fileError.value = ''
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['xlsx', 'csv'].includes(ext)) {
    fileError.value = 'Only .xlsx and .csv files are supported.'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    fileError.value = 'File exceeds the 10 MB limit.'
    return
  }
  selectedFile.value = file
}

function clearFile() {
  selectedFile.value = null
  fileError.value    = ''
}

function formatSize(bytes) {
  if (bytes < 1024)        return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function addTag() {
  const t = tagInput.value.trim().toLowerCase().replace(/,/g, '')
  if (t && !context.value.tags.includes(t) && context.value.tags.length < 10) {
    context.value.tags.push(t)
  }
  tagInput.value = ''
}

function removeTag(tag) {
  context.value.tags = context.value.tags.filter(t => t !== tag)
}

function applySuggestion(s) {
  context.value.objective = s.objective
  context.value.tags      = [...s.tags]
}

function submitWizard() {
  emit('submit', { file: selectedFile.value, context: { ...context.value } })
}
</script>

<style scoped>
.wizard {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  max-width: 620px;
  margin: 0 auto;
  width: 100%;
  gap: 28px;
}

.wizard__welcome { text-align: center; }
.welcome-icon {
  width: 52px; height: 52px;
  margin: 0 auto 16px;
  background: rgba(37,99,235,0.12);
  border: 1px solid rgba(37,99,235,0.3);
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: var(--col-blue-400);
}
.welcome-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.welcome-sub {
  font-size: 0.9rem;
  color: var(--col-text-secondary);
  line-height: 1.6;
}

.wizard__card {
  width: 100%;
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-xl);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--col-border);
  border-radius: var(--radius-lg);
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--t-normal);
}
.drop-zone:hover,
.drop-zone--over {
  border-color: var(--col-blue-600);
  background: rgba(37,99,235,0.05);
}
.drop-zone--selected {
  border-style: solid;
  border-color: var(--col-blue-600);
  background: rgba(37,99,235,0.05);
}
.drop-zone__empty { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.drop-icon { color: var(--col-blue-400); margin-bottom: 4px; }
.drop-zone__label { font-size: 1rem; font-weight: 500; color: var(--col-text-primary); }
.drop-zone__hint  { font-size: 0.83rem; color: var(--col-text-secondary); }
.drop-zone__limit { font-size: 0.75rem; color: var(--col-text-dim); font-family: var(--font-mono); }

.drop-zone__selected {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}
.file-icon { font-size: 2rem; }
.file-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.file-name { font-size: 0.9rem; font-weight: 500; color: var(--col-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-size { font-size: 0.75rem; color: var(--col-text-dim); font-family: var(--font-mono); }
.clear-btn {
  background: none; border: none; cursor: pointer;
  color: var(--col-text-dim); font-size: 0.9rem;
  padding: 4px 8px; border-radius: 4px;
  transition: color var(--t-fast), background var(--t-fast);
}
.clear-btn:hover { color: var(--col-error); background: rgba(239,68,68,0.1); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
.error-msg { font-size: 0.82rem; color: var(--col-error); padding: 8px 12px; background: rgba(239,68,68,0.08); border-radius: var(--radius-sm); border-left: 2px solid var(--col-error); }

/* Step 2 form */
.step-header { display: flex; align-items: center; gap: 12px; margin-bottom: -4px; }
.back-btn { background: none; border: none; cursor: pointer; color: var(--col-text-dim); font-size: 0.85rem; padding: 0; transition: color var(--t-fast); }
.back-btn:hover { color: var(--col-text-primary); }
.step-file { font-size: 0.8rem; color: var(--col-text-dim); font-family: var(--font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.step-title { font-size: 1.05rem; font-weight: 600; }
.step-hint  { font-size: 0.83rem; color: var(--col-text-secondary); margin-top: -8px; }

.form-grid { display: flex; flex-direction: column; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.8rem; font-weight: 500; color: var(--col-text-secondary); }
.form-select,
.form-textarea {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.88rem;
  padding: 10px 12px;
  transition: border-color var(--t-fast);
  resize: vertical;
}
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--col-blue-600);
}
.form-select option { background: var(--col-elevated); }

.tags-input {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  transition: border-color var(--t-fast);
  min-height: 44px;
}
.tags-input:focus-within { border-color: var(--col-blue-600); }
.tags-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(37,99,235,0.2);
  color: var(--col-blue-400);
  border: 1px solid rgba(37,99,235,0.3);
  border-radius: var(--radius-full);
  padding: 2px 8px;
  font-size: 0.75rem;
}
.tag button { background: none; border: none; cursor: pointer; color: inherit; font-size: 0.7rem; padding: 0 2px; }
.tag-input {
  background: none;
  border: none;
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.85rem;
  width: 100%;
  outline: none;
}
.tag-input::placeholder { color: var(--col-text-dim); }
.field-hint { font-size: 0.75rem; color: var(--col-text-dim); }

/* Suggestions */
.wizard__suggestions { width: 100%; text-align: center; }
.suggestions-label { font-size: 0.75rem; color: var(--col-text-dim); font-family: var(--font-mono); margin-bottom: 10px; }
.suggestions-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
.suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  font-size: 0.82rem;
  color: var(--col-text-secondary);
  cursor: pointer;
  font-family: var(--font-body);
  transition: all var(--t-fast);
}
.suggestion-chip:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 11px 20px; border-radius: var(--radius-md); font-size: 0.88rem; font-weight: 500; font-family: var(--font-body); cursor: pointer; border: none; transition: all var(--t-fast); justify-content: center; }
.btn--primary { background: var(--col-blue-600); color: white; }
.btn--primary:hover { background: var(--col-blue-700); }
.btn--primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn--full { width: 100%; }
</style>
