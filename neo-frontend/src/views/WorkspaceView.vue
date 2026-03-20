<template>
  <div class="workspace">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar--collapsed': sidebarCollapsed }">
      <div class="sidebar__head">
        <router-link to="/" class="sidebar__logo">
          <span class="logo-mark">N</span>
          <span v-if="!sidebarCollapsed" class="logo-text">eo</span>
        </router-link>
        <button class="icon-btn" @click="sidebarCollapsed = !sidebarCollapsed" title="Toggle sidebar">
          <IconMenu />
        </button>
      </div>

      <button class="new-chat-btn" @click="startNewDashboard" :title="sidebarCollapsed ? 'New Dashboard' : ''">
        <IconPlus />
        <span v-if="!sidebarCollapsed">New Dashboard</span>
      </button>

      <div v-if="!sidebarCollapsed" class="sidebar__section-label">Recent</div>

      <nav class="sidebar__sessions">
        <TransitionGroup name="session-list">
          <div
            v-for="session in store.sessions"
            :key="session.chat_id"
            class="session-item"
            :class="{ 'session-item--active': store.activeId === session.chat_id }"
            @click="loadSession(session)"
          >
            <IconChat class="session-item__icon" />
            <div v-if="!sidebarCollapsed" class="session-item__body">
              <span class="session-item__name">{{ session.name }}</span>
              <span class="session-item__meta">{{ session.dashboard_count }} dashboard{{ session.dashboard_count !== 1 ? 's' : '' }}</span>
            </div>
            <button
              v-if="!sidebarCollapsed"
              class="session-item__delete"
              @click.stop="confirmDelete(session)"
              title="Delete"
            >
              <IconTrash />
            </button>
          </div>
        </TransitionGroup>

        <div v-if="!store.sessions.length && !sidebarCollapsed" class="sidebar__empty">
          <span>No saved sessions</span>
          <span class="text-dim" style="font-size:0.75rem">Sign in to save your analyses</span>
        </div>
      </nav>

      <div v-if="!sidebarCollapsed" class="sidebar__foot">
        <button v-if="!authStore.isAuthenticated" class="sign-in-btn" @click="$router.push('/auth')">
          <IconUser />
          Sign in to save
        </button>
        <div v-else class="user-pill">
          <div class="user-pill__avatar">{{ authStore.user?.email?.[0]?.toUpperCase() || 'U' }}</div>
          <span class="truncate">{{ authStore.user?.email }}</span>
          <button class="icon-btn-sm" @click="authStore.logout()" title="Sign out">
            <IconLogout />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="workspace__main">
      <!-- Upload wizard phase -->
      <Transition name="fade" mode="out-in">
        <UploadWizard
          v-if="store.phase === 'idle'"
          key="wizard"
          @submit="handleFileSubmit"
        />
        <ProcessingScreen
          v-else-if="store.isProcessing"
          key="processing"
          :pct="store.uploadPct"
          :phase="store.phase"
        />
        <DashboardPanel
          v-else-if="store.phase === 'dashboard' || store.phase === 'summarizing'"
          key="dashboard"
        />
      </Transition>
    </main>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click="deleteTarget = null">
        <div class="modal" @click.stop>
          <h3>Delete "{{ deleteTarget.name }}"?</h3>
          <p>This will permanently delete all dashboards in this session.</p>
          <div class="modal__actions">
            <button class="btn btn--ghost" @click="deleteTarget = null">Cancel</button>
            <button class="btn btn--danger" @click="executeDelete">Delete</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'
import UploadWizard from '@/components/chat/UploadWizard.vue'
import ProcessingScreen from '@/components/chat/ProcessingScreen.vue'
import DashboardPanel from '@/components/dashboard/DashboardPanel.vue'
import IconMenu from '@/components/ui/IconMenu.vue'
import IconPlus from '@/components/ui/IconPlus.vue'
import IconChat from '@/components/ui/IconChat.vue'
import IconTrash from '@/components/ui/IconTrash.vue'
import IconUser from '@/components/ui/IconUser.vue'
import IconLogout from '@/components/ui/IconLogout.vue'

const store     = useWorkspaceStore()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const deleteTarget     = ref(null)

onMounted(() => store.fetchSessions())

function startNewDashboard() {
  store.resetToIdle()
}

function loadSession(session) {
  store.activeId = session.chat_id
  // In a full implementation: load dashboard from session
}

function handleFileSubmit({ file, context }) {
  store.userContext = context
  store.runAnalysis(file)
}

function confirmDelete(session) {
  deleteTarget.value = session
}

async function executeDelete() {
  if (!deleteTarget.value) return
  await store.removeSession(deleteTarget.value.chat_id)
  deleteTarget.value = null
}
</script>

<style scoped>
/* ── Workspace layout ─────────────────────────────────────── */
.workspace {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--col-base);
}

/* ── Sidebar ──────────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--col-surface);
  border-right: 1px solid var(--col-border);
  transition: width var(--t-normal), min-width var(--t-normal);
  overflow: hidden;
}
.sidebar--collapsed {
  width: 60px;
  min-width: 60px;
}
.sidebar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-bottom: 1px solid var(--col-border);
  min-height: var(--header-h);
}
.sidebar__logo {
  display: flex;
  align-items: baseline;
  gap: 2px;
  text-decoration: none;
}
.logo-mark {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #60A5FA, #2563EB);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-text {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--col-text-primary);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 12px;
  padding: 10px 14px;
  background: var(--col-blue-600);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--t-fast), box-shadow var(--t-fast);
  white-space: nowrap;
  overflow: hidden;
}
.new-chat-btn:hover {
  background: var(--col-blue-700);
  box-shadow: 0 0 16px rgba(37,99,235,0.4);
}

.sidebar__section-label {
  padding: 8px 16px 4px;
  font-size: 0.7rem;
  font-family: var(--font-mono);
  color: var(--col-text-dim);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sidebar__sessions {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--t-fast);
  position: relative;
}
.session-item:hover { background: var(--col-elevated); }
.session-item--active { background: rgba(37,99,235,0.15); }
.session-item--active .session-item__name { color: var(--col-blue-400); }
.session-item__icon { flex-shrink: 0; color: var(--col-text-dim); width: 16px; height: 16px; }
.session-item__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.session-item__name {
  font-size: 0.83rem;
  color: var(--col-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-item__meta {
  font-size: 0.7rem;
  color: var(--col-text-dim);
  font-family: var(--font-mono);
}
.session-item__delete {
  opacity: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--col-text-dim);
  padding: 2px;
  border-radius: 4px;
  transition: opacity var(--t-fast), color var(--t-fast);
  flex-shrink: 0;
}
.session-item:hover .session-item__delete { opacity: 1; }
.session-item__delete:hover { color: var(--col-error); }

.sidebar__empty {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 20px 12px;
  font-size: 0.82rem;
  color: var(--col-text-dim);
}

.sidebar__foot {
  padding: 12px;
  border-top: 1px solid var(--col-border);
}
.sign-in-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-secondary);
  font-family: var(--font-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: border-color var(--t-fast), color var(--t-fast);
}
.sign-in-btn:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }
.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: var(--radius-md);
  font-size: 0.82rem;
  color: var(--col-text-secondary);
  overflow: hidden;
}
.user-pill__avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--col-blue-600);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

/* ── Main ─────────────────────────────────────────────────── */
.workspace__main {
  flex: 1;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

/* ── Buttons / Icons ──────────────────────────────────────── */
.icon-btn {
  background: none;
  border: none;
  color: var(--col-text-dim);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: color var(--t-fast), background var(--t-fast);
  display: flex;
  align-items: center;
}
.icon-btn:hover { color: var(--col-text-primary); background: var(--col-elevated); }
.icon-btn-sm {
  background: none;
  border: none;
  color: var(--col-text-dim);
  cursor: pointer;
  padding: 3px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}
.icon-btn-sm:hover { color: var(--col-error); }

.btn { display: inline-flex; align-items: center; gap: 8px; padding: 9px 18px; border-radius: var(--radius-md); font-size: 0.88rem; font-weight: 500; font-family: var(--font-body); cursor: pointer; border: none; transition: all var(--t-fast); }
.btn--ghost { background: transparent; color: var(--col-text-secondary); border: 1px solid var(--col-border); }
.btn--ghost:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }
.btn--danger { background: var(--col-error); color: white; }
.btn--danger:hover { background: #DC2626; }

/* ── Modal ─────────────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}
.modal {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-lg);
  padding: 28px;
  max-width: 420px;
  width: 90%;
  animation: fadeIn 0.2s ease;
}
.modal h3 { font-size: 1rem; margin-bottom: 8px; }
.modal p  { font-size: 0.88rem; color: var(--col-text-secondary); margin-bottom: 24px; }
.modal__actions { display: flex; gap: 10px; justify-content: flex-end; }

/* ── Session list transition ───────────────────────────────── */
.session-list-enter-active,
.session-list-leave-active { transition: all 0.2s ease; }
.session-list-enter-from,
.session-list-leave-to { opacity: 0; transform: translateX(-8px); }
</style>
