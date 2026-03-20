<template>
  <div class="processing">
    <div class="processing__card">
      <!-- Animated rings -->
      <div class="rings" aria-hidden="true">
        <div class="ring ring--1" />
        <div class="ring ring--2" />
        <div class="ring ring--3" />
        <div class="ring__core">
          <span class="ring__letter">N</span>
        </div>
      </div>

      <h2 class="processing__title">{{ currentMessage }}</h2>

      <!-- Progress bar (upload phase) -->
      <div v-if="phase === 'uploading'" class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: pct + '%' }" />
        </div>
        <span class="progress-label mono">{{ pct }}%</span>
      </div>

      <!-- Steps list -->
      <div class="steps-list">
        <div
          v-for="(step, i) in steps"
          :key="i"
          class="step-row"
          :class="{
            'step-row--done':    i < currentStep,
            'step-row--active':  i === currentStep,
            'step-row--pending': i > currentStep
          }"
        >
          <div class="step-row__icon">
            <span v-if="i < currentStep">✓</span>
            <span v-else-if="i === currentStep" class="spinner" />
            <span v-else>○</span>
          </div>
          <span class="step-row__label">{{ step }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  pct:   { type: Number, default: 0 },
  phase: { type: String, default: 'uploading' }
})

const steps = [
  'Uploading file',
  'Detecting table structure',
  'Cleaning & normalising data',
  'AI schema detection',
  'Extracting KPIs & trends',
  'Building chart configurations'
]

const currentStep = computed(() => {
  if (props.phase === 'uploading') return props.pct < 100 ? 0 : 1
  return 3
})

const messages = [
  'Parsing your data…',
  'Running AI schema detection…',
  'Computing KPIs and trends…',
  'Almost ready…'
]

const currentMessage = computed(() => messages[currentStep.value] || 'Processing…')
</script>

<style scoped>
.processing {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}
.processing__card {
  max-width: 400px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
}

/* Rings animation */
.rings {
  position: relative;
  width: 96px; height: 96px;
}
.ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid transparent;
}
.ring--1 {
  inset: 0;
  border-color: rgba(37,99,235,0.6);
  animation: spin 2.4s linear infinite;
}
.ring--2 {
  inset: 10px;
  border-color: rgba(37,99,235,0.3);
  animation: spin 1.8s linear infinite reverse;
}
.ring--3 {
  inset: 20px;
  border-color: rgba(37,99,235,0.15);
  animation: spin 3s linear infinite;
}
.ring__core {
  position: absolute;
  inset: 30px;
  background: var(--col-blue-600);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring__letter {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1rem;
  color: white;
}

.processing__title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--col-text-secondary);
  text-align: center;
  font-family: var(--font-mono);
}

/* Progress */
.progress-wrap { width: 100%; display: flex; flex-direction: column; gap: 8px; align-items: center; }
.progress-bar {
  width: 100%;
  height: 3px;
  background: var(--col-border);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--col-blue-600), var(--col-blue-400));
  border-radius: 2px;
  transition: width 0.3s ease;
}
.progress-label { font-size: 0.75rem; color: var(--col-blue-400); }

/* Steps */
.steps-list { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.step-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  transition: all var(--t-normal);
}
.step-row--done    { opacity: 0.5; }
.step-row--active  { background: rgba(37,99,235,0.08); }
.step-row--pending { opacity: 0.25; }
.step-row__icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: var(--col-blue-400);
  flex-shrink: 0;
}
.step-row--done .step-row__icon { color: var(--col-success); }
.step-row__label { font-size: 0.83rem; color: var(--col-text-secondary); }
.step-row--active .step-row__label { color: var(--col-text-primary); font-weight: 500; }
.spinner {
  display: block;
  width: 14px; height: 14px;
  border: 1.5px solid var(--col-blue-400);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.mono { font-family: var(--font-mono); }
</style>
