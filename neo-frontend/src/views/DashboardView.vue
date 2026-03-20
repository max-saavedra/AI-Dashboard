<template>
  <div class="dashboard-page">
    <div class="dash-nav">
      <router-link to="/workspace" class="back-link">
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"/>
        </svg>
        Back to workspace
      </router-link>
      <div class="dash-logo">
        <span class="logo-mark">N</span><span class="logo-text">eo</span>
      </div>
    </div>
    <DashboardPanel v-if="store.hasDashboard" />
    <div v-else class="no-dashboard">
      <p>No dashboard loaded. <router-link to="/workspace">Go to workspace</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { useWorkspaceStore } from '@/stores/workspace'
import DashboardPanel from '@/components/dashboard/DashboardPanel.vue'

const store = useWorkspaceStore()
</script>

<style scoped>
.dashboard-page { min-height: 100vh; display: flex; flex-direction: column; }
.dash-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--col-border);
  background: var(--col-surface);
}
.back-link {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.85rem; color: var(--col-text-secondary);
  text-decoration: none;
  transition: color var(--t-fast);
}
.back-link:hover { color: var(--col-text-primary); }
.dash-logo { display: flex; align-items: baseline; }
.logo-mark {
  font-family: var(--font-mono); font-size: 1.1rem; font-weight: 700;
  background: linear-gradient(135deg, #60A5FA, #2563EB);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.logo-text { font-family: var(--font-display); font-size: 1.1rem; font-weight: 800; color: var(--col-text-primary); }
.no-dashboard { flex: 1; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; color: var(--col-text-dim); }
</style>
