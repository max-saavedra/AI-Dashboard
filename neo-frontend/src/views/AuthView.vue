<template>
  <div class="auth-page">
    <div class="auth-bg" aria-hidden="true">
      <div class="bg-orb bg-orb--1" />
      <div class="bg-orb bg-orb--2" />
      <div class="bg-grid" />
    </div>

    <div class="auth-card">
      <!-- Logo -->
      <router-link to="/" class="auth-logo">
        <span class="logo-mark">N</span>
        <span class="logo-text">eo</span>
      </router-link>

      <h1 class="auth-title">{{ isSignUp ? 'Create your account' : 'Welcome back' }}</h1>
      <p class="auth-sub">
        {{ isSignUp
          ? 'Sign up to save your analyses and access history.'
          : 'Sign in to access your saved dashboards.' }}
      </p>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-field">
          <label class="form-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="you@company.com"
            autocomplete="email"
            required
          />
        </div>

        <div class="form-field">
          <label class="form-label">Password</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••••"
            autocomplete="current-password"
            required
            minlength="8"
          />
        </div>

        <div v-if="error" class="auth-error">{{ error }}</div>

        <button type="submit" class="auth-btn" :disabled="loading">
          <span v-if="loading" class="spinner" />
          {{ loading ? 'Please wait…' : (isSignUp ? 'Create account' : 'Sign in') }}
        </button>
      </form>

      <p class="auth-switch">
        {{ isSignUp ? 'Already have an account?' : "Don't have an account?" }}
        <button class="link-btn" @click="isSignUp = !isSignUp">
          {{ isSignUp ? 'Sign in' : 'Sign up' }}
        </button>
      </p>

      <div class="auth-divider"><span>or</span></div>

      <button class="ghost-btn" @click="$router.push('/workspace')">
        Continue without account
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"/>
        </svg>
      </button>

      <p class="auth-note">Anonymous sessions are kept for 24 hours.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, signup } from '@/services/authService'

const router = useRouter()

const isSignUp = ref(false)
const email    = ref('')
const password = ref('')
const loading  = ref(false)
const error    = ref('')

async function handleSubmit() {
  error.value   = ''
  loading.value = true

  try {
    if (password.value.length < 8) {
      throw new Error('Password must be at least 8 characters.')
    }

    if (isSignUp.value) {
      // Call real signup endpoint
      await signup(email.value, password.value)
      console.log('✓ Account created successfully')
    } else {
      // Call real login endpoint
      await login(email.value, password.value)
      console.log('✓ Logged in successfully')
    }

    // Redirect to workspace on success
    router.push('/workspace')

  } catch (err) {
    error.value = err.message || 'Authentication failed. Please try again.'
    console.error('Auth error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
}
.auth-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.1;
}
.bg-orb--1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #2563EB, transparent 70%);
  top: -150px; right: -100px;
}
.bg-orb--2 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #1D4ED8, transparent 70%);
  bottom: -80px; left: -60px;
}
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(37,99,235,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,99,235,0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}

.auth-card {
  position: relative;
  z-index: 10;
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-xl);
  padding: 40px;
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.4s ease;
}

.auth-logo {
  display: flex;
  align-items: baseline;
  gap: 2px;
  text-decoration: none;
  margin-bottom: 4px;
}
.logo-mark {
  font-family: var(--font-mono);
  font-size: 1.4rem;
  font-weight: 700;
  background: linear-gradient(135deg, #60A5FA, #2563EB);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-text {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--col-text-primary);
}

.auth-title { font-size: 1.3rem; font-weight: 700; }
.auth-sub   { font-size: 0.88rem; color: var(--col-text-secondary); line-height: 1.5; margin-top: -8px; }

.auth-form { display: flex; flex-direction: column; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.8rem; font-weight: 500; color: var(--col-text-secondary); }
.form-input {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.9rem;
  padding: 11px 14px;
  transition: border-color var(--t-fast);
}
.form-input:focus { outline: none; border-color: var(--col-blue-600); }
.form-input::placeholder { color: var(--col-text-dim); }

.auth-error {
  font-size: 0.82rem;
  color: var(--col-error);
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-md);
  padding: 9px 12px;
}

.auth-btn {
  width: 100%;
  padding: 12px;
  background: var(--col-blue-600);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-family: var(--font-body);
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background var(--t-fast), box-shadow var(--t-fast);
}
.auth-btn:hover:not(:disabled) {
  background: var(--col-blue-700);
  box-shadow: 0 0 20px rgba(37,99,235,0.3);
}
.auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.auth-switch {
  font-size: 0.85rem;
  color: var(--col-text-secondary);
  text-align: center;
}
.link-btn {
  background: none; border: none;
  color: var(--col-blue-400);
  cursor: pointer;
  font-family: var(--font-body);
  font-size: inherit;
  padding: 0;
  transition: color var(--t-fast);
}
.link-btn:hover { color: var(--col-blue-100); }

.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--col-text-dim);
  font-size: 0.78rem;
}
.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--col-border);
}

.ghost-btn {
  width: 100%;
  padding: 11px;
  background: transparent;
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-secondary);
  font-family: var(--font-body);
  font-size: 0.88rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all var(--t-fast);
}
.ghost-btn:hover {
  border-color: var(--col-blue-600);
  color: var(--col-text-primary);
}

.auth-note {
  font-size: 0.72rem;
  color: var(--col-text-dim);
  text-align: center;
  font-family: var(--font-mono);
}
</style>
