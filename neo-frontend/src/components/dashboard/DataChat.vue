<template>
  <div class="data-chat" :class="{ 'data-chat--expanded': expanded }">
    <!-- Toggle bar -->
    <button class="chat-toggle" @click="expanded = !expanded">
      <div class="chat-toggle__left">
        <div class="chat-icon">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
          </svg>
        </div>
        <span class="chat-toggle__label">Ask about this data</span>
        <span v-if="store.qaHistory.length" class="chat-badge">{{ Math.floor(store.qaHistory.length / 2) }}</span>
      </div>
      <svg
        class="chevron"
        :class="{ 'chevron--up': expanded }"
        viewBox="0 0 20 20" fill="currentColor" width="14" height="14"
      >
        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
      </svg>
    </button>

    <!-- Chat body -->
    <Transition name="chat-expand">
      <div v-if="expanded" class="chat-body">
        <!-- Messages -->
        <div ref="messagesEl" class="chat-messages">
          <!-- Welcome message -->
          <div v-if="!store.qaHistory.length" class="chat-welcome">
            <p>Ask me anything about your data. For example:</p>
            <div class="suggestion-pills">
              <button
                v-for="s in suggestions"
                :key="s"
                class="suggestion-pill"
                @click="sendSuggestion(s)"
              >{{ s }}</button>
            </div>
          </div>

          <!-- Messages -->
          <div
            v-for="(msg, i) in store.qaHistory"
            :key="i"
            class="chat-msg"
            :class="`chat-msg--${msg.role}`"
          >
            <div v-if="msg.role === 'assistant'" class="msg-avatar">N</div>
            <div class="msg-bubble">{{ msg.content }}</div>
            <div v-if="msg.role === 'user'" class="msg-avatar msg-avatar--user">
              {{ userInitial }}
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="isTyping" class="chat-msg chat-msg--assistant">
            <div class="msg-avatar">N</div>
            <div class="msg-bubble msg-bubble--typing">
              <span class="dot" />
              <span class="dot" style="animation-delay: 0.15s" />
              <span class="dot" style="animation-delay: 0.3s" />
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="chat-input-row">
          <input
            ref="inputEl"
            v-model="question"
            class="chat-input"
            placeholder="What is the highest revenue region?"
            :disabled="isTyping"
            @keydown.enter.prevent="sendQuestion"
          />
          <button
            class="send-btn"
            :disabled="!question.trim() || isTyping"
            @click="sendQuestion"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
            </svg>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'

const store    = useWorkspaceStore()
const auth     = useAuthStore()
const expanded = ref(false)
const question = ref('')
const isTyping = ref(false)
const messagesEl = ref(null)
const inputEl    = ref(null)

const userInitial = computed(() =>
  auth.user?.email?.[0]?.toUpperCase() || 'U'
)

const suggestions = computed(() => {
  const kpis = Object.keys(store.result?.kpis?.kpis || {})
  const dims  = store.result?.kpis?.dimensions || []
  const base  = ['What is the total?', 'Which category performs best?', 'What are the main trends?']
  if (kpis.length && dims.length) {
    return [
      `What is the highest ${kpis[0]}?`,
      `Which ${dims[0]} has the most ${kpis[0]}?`,
      'What trends do you see in the data?'
    ]
  }
  return base
})

async function sendQuestion() {
  const q = question.value.trim()
  if (!q || isTyping.value) return
  question.value = ''
  isTyping.value = true
  expanded.value = true

  await nextTick()
  scrollToBottom()

  await store.sendQuestion(q)
  isTyping.value = false

  await nextTick()
  scrollToBottom()
  inputEl.value?.focus()
}

function sendSuggestion(s) {
  question.value = s
  sendQuestion()
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}
</script>

<style scoped>
.data-chat {
  border-top: 1px solid var(--col-border);
  background: var(--col-surface);
  transition: all var(--t-normal);
  flex-shrink: 0;
}

/* Toggle bar */
.chat-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--col-text-secondary);
  font-family: var(--font-body);
  transition: background var(--t-fast);
}
.chat-toggle:hover { background: var(--col-elevated); color: var(--col-text-primary); }
.chat-toggle__left { display: flex; align-items: center; gap: 10px; }
.chat-icon {
  width: 26px; height: 26px;
  background: rgba(37,99,235,0.15);
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--col-blue-400);
}
.chat-toggle__label { font-size: 0.88rem; font-weight: 500; }
.chat-badge {
  background: var(--col-blue-600);
  color: white;
  font-size: 0.65rem;
  font-family: var(--font-mono);
  padding: 1px 6px;
  border-radius: var(--radius-full);
}
.chevron { transition: transform var(--t-fast); color: var(--col-text-dim); }
.chevron--up { transform: rotate(180deg); }

/* Chat body */
.chat-body {
  display: flex;
  flex-direction: column;
  height: 320px;
  border-top: 1px solid var(--col-border);
}

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chat-welcome {
  color: var(--col-text-dim);
  font-size: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.suggestion-pills { display: flex; flex-wrap: wrap; gap: 6px; }
.suggestion-pill {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-full);
  color: var(--col-text-secondary);
  font-family: var(--font-body);
  font-size: 0.78rem;
  padding: 5px 12px;
  cursor: pointer;
  transition: all var(--t-fast);
}
.suggestion-pill:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }

/* Message rows */
.chat-msg {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  animation: fadeIn 0.2s ease;
}
.chat-msg--user { flex-direction: row-reverse; }

.msg-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--col-blue-600);
  color: white;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.msg-avatar--user {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  color: var(--col-text-secondary);
}

.msg-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  font-size: 0.85rem;
  line-height: 1.55;
}
.chat-msg--assistant .msg-bubble {
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  color: var(--col-text-primary);
  border-bottom-left-radius: var(--radius-sm);
}
.chat-msg--user .msg-bubble {
  background: var(--col-blue-600);
  color: white;
  border-bottom-right-radius: var(--radius-sm);
}

/* Typing dots */
.msg-bubble--typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 14px;
}
.dot {
  display: block;
  width: 6px; height: 6px;
  background: var(--col-text-dim);
  border-radius: 50%;
  animation: dot-bounce 1.2s infinite ease-in-out;
}

/* Input */
.chat-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-top: 1px solid var(--col-border);
}
.chat-input {
  flex: 1;
  background: var(--col-elevated);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-full);
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.88rem;
  padding: 9px 16px;
  outline: none;
  transition: border-color var(--t-fast);
}
.chat-input:focus { border-color: var(--col-blue-600); }
.chat-input::placeholder { color: var(--col-text-dim); }
.chat-input:disabled { opacity: 0.5; cursor: not-allowed; }

.send-btn {
  width: 36px; height: 36px;
  background: var(--col-blue-600);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: background var(--t-fast), transform var(--t-fast);
}
.send-btn:hover:not(:disabled) { background: var(--col-blue-700); transform: scale(1.05); }
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* Expand transition */
.chat-expand-enter-active, .chat-expand-leave-active { transition: all 0.25s ease; overflow: hidden; }
.chat-expand-enter-from, .chat-expand-leave-to { opacity: 0; height: 0 !important; }
</style>
