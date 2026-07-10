<template>
  <!-- Toast -->
  <div v-if="toast.show" class="toast" :class="'toast-' + toast.type">{{ toast.message }}</div>

  <!-- Auth Page -->
  <div v-if="!isLoggedIn" class="auth-page">
    <div class="auth-card">
      <div class="auth-lang-toggle">
        <button class="btn btn-ghost btn-sm" @click="toggleLang">{{ lang === 'zh' ? 'EN' : '中文' }}</button>
      </div>
      <div class="auth-logo">✦</div>
      <h1 class="auth-title">Blink</h1>
      <p class="auth-subtitle">{{ isLoginMode ? t.signInTo : t.createAccount }}</p>

      <form @submit.prevent="handleAuth" class="auth-form" autocomplete="off">
        <div class="form-group">
          <label class="form-label">{{ t.username }}</label>
          <input
            v-model="authForm.username"
            type="text"
            class="input"
            :placeholder="t.usernameHint"
            autocomplete="off"
            required
            minlength="3"
          />
        </div>
        <div class="form-group">
          <label class="form-label">{{ t.password }}</label>
          <input
            v-model="authForm.password"
            type="password"
            class="input"
            :placeholder="t.passwordHint"
            autocomplete="new-password"
            required
            minlength="6"
          />
        </div>
        <div v-if="authError" class="form-error">{{ authError }}</div>
        <button type="submit" class="btn btn-primary auth-submit" :disabled="authLoading">
          <span v-if="authLoading" class="spinner" style="width:16px;height:16px;border-width:2px"></span>
          {{ authLoading ? '' : (isLoginMode ? t.signIn : t.createAccount) }}
        </button>
      </form>

      <div class="auth-switch">
        <span v-if="isLoginMode">
          {{ t.noAccount }} <button class="link-btn" @click="isLoginMode = false">{{ t.signUp }}</button>
        </span>
        <span v-else>
          {{ t.hasAccount }} <button class="link-btn" @click="isLoginMode = true">{{ t.signIn }}</button>
        </span>
      </div>
    </div>
  </div>

  <!-- Main App -->
  <div v-else class="app-layout">
    <!-- Top Bar -->
    <header class="topbar">
      <div class="topbar-left">
        <span class="topbar-logo">✦</span>
        <span class="topbar-brand">Blink</span>
      </div>
      <div class="topbar-right">
        <button class="btn btn-ghost btn-sm" @click="showModelConfig = true" :title="t.settings">⚙</button>
        <button class="btn btn-ghost btn-sm" @click="toggleLang">{{ lang === 'zh' ? 'EN' : '中文' }}</button>
        <button class="btn btn-primary btn-sm" @click="handleNewWorkflow">+ {{ t.new }}</button>
        <button class="btn btn-ghost btn-sm" @click="handleLogout">{{ t.signOut }}</button>
      </div>
    </header>

    <div class="main-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-title">{{ t.history }}</div>
        <div v-if="loadingThreads" class="loading-state">
          <div class="spinner"></div>
        </div>
        <div v-else-if="threadList.length === 0" class="sidebar-empty">
          <div class="sidebar-empty-icon">📄</div>
          <div class="text-muted text-sm">{{ t.noWorkflows }}</div>
        </div>
        <div v-else class="thread-list">
          <div
            v-for="thread in threadList"
            :key="thread.thread_id"
            class="thread-item"
            :class="{ active: currentThreadId === thread.thread_id }"
            @click="handleResumeWorkflow(thread.thread_id)"
          >
            <!-- Edit Mode -->
            <template v-if="editingThreadId === thread.thread_id">
              <input
                v-model="editingName"
                class="thread-rename-input"
                @click.stop
                @keydown.enter="confirmRename(thread.thread_id)"
                @keydown.escape="cancelRename"
                ref="renameInput"
                maxlength="200"
              />
              <div class="thread-edit-actions">
                <button class="thread-action-btn" @click.stop="confirmRename(thread.thread_id)" title="Confirm">✓</button>
                <button class="thread-action-btn" @click.stop="cancelRename" title="Cancel">✕</button>
              </div>
            </template>
            <!-- Display Mode -->
            <template v-else>
              <div class="thread-info">
                <div class="thread-name">{{ thread.name || thread.selected_topic || thread.topic_direction || t.untitled }}</div>
                <span class="badge" :class="getStatusBadgeClass(thread.status)">{{ getStatusText(thread.status) }}</span>
              </div>
              <div class="thread-actions">
                <button class="thread-action-btn" @click.stop="startRename(thread)" title="Rename">✏️</button>
                <button class="thread-action-btn" @click.stop="handleDeleteThread(thread.thread_id)" title="Delete">🗑️</button>
              </div>
            </template>
          </div>
        </div>
      </aside>

      <!-- Content Area -->
      <main class="content">
        <!-- Empty State -->
        <div v-if="!currentWorkflow" class="empty-state">
          <div class="empty-state-content">
            <div class="empty-state-icon">✦</div>
            <h2>{{ t.startCreate }}</h2>
            <p class="text-muted">{{ t.startDesc }}</p>
            <div class="start-form">
              <input
                v-model="topicDirection"
                type="text"
                class="input"
                placeholder="AI, Python, Vue.js..."
                @keydown.enter="handleStartWorkflow"
              />
              <label class="toggle-label">
                <input type="checkbox" v-model="generateImages" class="toggle-checkbox" />
                <span class="toggle-text">{{ t.generateImages || '生成配图' }}</span>
              </label>
              <button
                class="btn btn-primary"
                :disabled="!topicDirection || startingWorkflow"
                @click="handleStartWorkflow"
              >
                <span v-if="startingWorkflow" class="spinner" style="width:16px;height:16px;border-width:2px;border-top-color:#fff"></span>
                {{ startingWorkflow ? '' : t.generate }}
              </button>
            </div>
          </div>
        </div>

        <!-- Workflow Content -->
        <div v-else class="workflow-content">
          <!-- Header -->
          <div class="workflow-header">
            <div>
              <h1 class="workflow-title">{{ currentWorkflow.topic_direction || t.contentWorkflow }}</h1>
              <span class="badge" :class="getStatusBadgeClass(currentWorkflow.status)">{{ getStatusText(currentWorkflow.status) }}</span>
            </div>
          </div>

          <!-- Topic Selection -->
          <div v-if="currentWorkflow.status === 'topics_generated'" class="workflow-section">
            <h2 class="section-title">{{ t.selectTopic }}</h2>
            <p class="text-muted mb-6">{{ t.selectTopicDesc }}</p>
            <div class="topic-grid">
              <div
                v-for="(topic, index) in currentWorkflow.generated_topics"
                :key="index"
                class="topic-card"
                :class="{ selected: selectedTopic === topic }"
                @click="selectedTopic = topic"
              >
                <div class="topic-index">{{ index + 1 }}</div>
                <div class="topic-text">{{ topic }}</div>
              </div>
            </div>
            <div class="action-bar">
              <button class="btn btn-primary" :disabled="!selectedTopic" @click="handleSelectTopic">{{ t.confirmTopic }}</button>
              <button class="btn btn-secondary" @click="handleRefreshTopics" :disabled="workflowLoading">🔄 {{ t.refreshTopics || '换一批' }}</button>
            </div>
          </div>

          <!-- Article Preview -->
          <div v-if="currentWorkflow.status === 'draft_generated' || currentWorkflow.status === 'evaluated'" class="workflow-section">
            <h2 class="section-title">{{ t.articlePreview }}</h2>

            <!-- Quality Scores -->
            <div v-if="currentWorkflow.quality_score && Object.keys(currentWorkflow.quality_score).length > 0" class="score-grid">
              <div v-for="(item, key) in scoreItems" :key="key" class="score-card">
                <div class="score-header">
                  <span class="score-label">{{ item.label }}</span>
                  <span class="score-value">{{ currentWorkflow.quality_score[key] }}/10</span>
                </div>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (currentWorkflow.quality_score[key] * 10) + '%' }"></div>
                </div>
              </div>
            </div>

            <!-- Article -->
            <div class="article-card">
              <div class="article-toolbar">
                <button class="btn btn-ghost btn-sm" @click="copyArticle(currentWorkflow.article_content)">📋 {{ t.copy }}</button>
              </div>
              <div class="article-body" v-html="formatArticle(currentWorkflow.article_content)"></div>
            </div>

            <div class="action-bar">
              <button class="btn btn-primary" @click="handleApprove">{{ t.approve }}</button>
              <button class="btn btn-secondary" @click="showRejectDialog = true">{{ t.requestChanges }}</button>
            </div>
          </div>

          <!-- Completed -->
          <div v-if="currentWorkflow.status === 'completed'" class="workflow-section">
            <h2 class="section-title">{{ t.contentReady }}</h2>
            <div class="article-card">
              <div class="article-toolbar">
                <button class="btn btn-ghost btn-sm" @click="copyArticle(currentWorkflow.article_content)">📋 {{ t.copy }}</button>
              </div>
              <div class="article-body" v-html="formatArticle(currentWorkflow.article_content)"></div>
            </div>

            <div v-if="currentWorkflow.image_urls && currentWorkflow.image_urls.length > 0" class="mt-6">
              <h3 class="section-title" style="font-size:16px">{{ t.generatedVisuals }}</h3>
              <div class="image-grid">
                <div v-for="(url, index) in currentWorkflow.image_urls" :key="index" class="image-card">
                  <img :src="url" :alt="'Visual ' + (index + 1)" @error="$event.target.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22><rect fill=%22%23f3f4f6%22 width=%22200%22 height=%22200%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%239ca3af%22 font-size=%2214%22>Image</text></svg>'" />
                  <button class="btn btn-ghost btn-sm" @click="downloadImage(url, 'visual_' + (index + 1) + '.png')">⬇ {{ t.download }}</button>
                </div>
              </div>
              <div class="action-bar">
                <button class="btn btn-secondary" @click="handleRefreshImages" :disabled="workflowLoading">🔄 {{ t.refreshImages || '换一批配图' }}</button>
              </div>
            </div>

            <div class="action-bar">
              <button class="btn btn-primary" @click="handleNewWorkflow">{{ t.createNew }}</button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="workflowLoading" class="loading-state">
            <div class="spinner"></div>
            <span>{{ t.processing }}</span>
          </div>
        </div>
      </main>
    </div>

    <!-- Reject Dialog -->
    <div v-if="showRejectDialog" class="dialog-overlay" @click.self="showRejectDialog = false">
      <div class="dialog">
        <h3 class="dialog-title">{{ t.requestChanges }}</h3>
        <div class="form-group">
          <label class="form-label">{{ t.feedback }}</label>
          <textarea v-model="rejectFeedback" class="input" rows="4" :placeholder="t.feedbackPlaceholder"></textarea>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" @click="showRejectDialog = false">{{ t.cancel }}</button>
          <button class="btn btn-primary" @click="handleReject">{{ t.submit }}</button>
        </div>
      </div>
    </div>

    <!-- Model Config Panel -->
    <ModelConfigPanel
      :visible="showModelConfig"
      @close="showModelConfig = false"
      @save="handleModelConfigSave"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import DOMPurify from 'dompurify'
import { authApi, workflowApi, isLoggedIn as checkLoggedIn } from './api.js'
import { useI18n } from './composables/useI18n.js'
import { useToast } from './composables/useToast.js'
import ModelConfigPanel from './components/ModelConfigPanel.vue'

export default {
  name: 'App',
  components: { ModelConfigPanel },
  setup() {
    // Auth
    const isLoggedIn = ref(false)
    const isLoginMode = ref(true)
    const authForm = reactive({ username: '', password: '' })
    const authError = ref('')
    const authLoading = ref(false)

    // Workflow
    const topicDirection = ref('')
    const generateImages = ref(true)
    const selectedTopic = ref('')
    const currentWorkflow = ref(null)
    const currentThreadId = ref(null)
    const threadList = ref([])
    const loadingThreads = ref(false)
    const startingWorkflow = ref(false)
    const workflowLoading = ref(false)
    const editingThreadId = ref(null)
    const editingName = ref('')

    // Dialog
    const showRejectDialog = ref(false)
    const rejectFeedback = ref('')

    // Model Config
    const showModelConfig = ref(false)
    const modelConfig = ref(JSON.parse(localStorage.getItem('modelConfig') || 'null'))

    // i18n
    const { lang, t, toggleLang } = useI18n()

    // Toast
    const { toast, showToast } = useToast()

    // Score items config (computed for i18n)
    const scoreItems = computed(() => ({
      relevance: { label: t.value.relevance },
      readability: { label: t.value.readability },
      depth: { label: t.value.depth },
      originality: { label: t.value.originality },
    }))

    // Init
    onMounted(async () => {
      if (checkLoggedIn()) {
        isLoggedIn.value = true
        await loadThreadList()
      }
      window.addEventListener('unauthorized', () => {
        isLoggedIn.value = false
        currentWorkflow.value = null
        currentThreadId.value = null
      })
    })

    // Auth
    async function handleAuth() {
      authError.value = ''
      authLoading.value = true
      try {
        if (isLoginMode.value) {
          await authApi.login(authForm.username, authForm.password)
        } else {
          await authApi.register(authForm.username, authForm.password)
          await authApi.login(authForm.username, authForm.password)
        }
        isLoggedIn.value = true
        await loadThreadList()
      } catch (error) {
        authError.value = error.message
      } finally {
        authLoading.value = false
      }
    }

    function handleLogout() {
      authApi.logout()
      isLoggedIn.value = false
      currentWorkflow.value = null
      currentThreadId.value = null
    }

    function handleModelConfigSave(config) {
      modelConfig.value = config
      showModelConfig.value = false
      showToast(config ? t.value.configSaved : t.value.configCleared, 'success')
    }

    // Threads
    async function loadThreadList() {
      loadingThreads.value = true
      try {
        const data = await workflowApi.list()
        threadList.value = data.threads || []
      } catch (error) {
        console.error('Failed to load threads:', error)
      } finally {
        loadingThreads.value = false
      }
    }

    function startRename(thread) {
      editingThreadId.value = thread.thread_id
      editingName.value = thread.name || thread.selected_topic || thread.topic_direction || ''
      nextTick(() => {
        const input = document.querySelector('.thread-rename-input')
        if (input) input.focus()
      })
    }

    function cancelRename() {
      editingThreadId.value = null
      editingName.value = ''
    }

    async function confirmRename(threadId) {
      const name = editingName.value.trim()
      if (!name) return
      try {
        await workflowApi.rename(threadId, name)
        const thread = threadList.value.find(t => t.thread_id === threadId)
        if (thread) thread.name = name
        cancelRename()
        showToast(t.value.renamed)
      } catch (error) {
        showToast('Rename failed: ' + error.message, 'error')
      }
    }

    async function handleDeleteThread(threadId) {
      if (!confirm(t.value.deleteConfirm)) return
      try {
        await workflowApi.delete(threadId)
        threadList.value = threadList.value.filter(t => t.thread_id !== threadId)
        if (currentThreadId.value === threadId) {
          currentWorkflow.value = null
          currentThreadId.value = null
        }
        showToast(t.value.deleted)
      } catch (error) {
        showToast(t.value.deleteFailed + ': ' + error.message, 'error')
      }
    }

    // Workflow
    async function handleStartWorkflow() {
      if (!topicDirection.value) return
      startingWorkflow.value = true
      try {
        const data = await workflowApi.start(topicDirection.value, generateImages.value, modelConfig.value)
        currentThreadId.value = data.thread_id
        currentWorkflow.value = mergeWorkflowData(data)
        await loadThreadList()
      } catch (error) {
        showToast(t.value.failedToStart + ': ' + error.message, 'error')
      } finally {
        startingWorkflow.value = false
      }
    }

    async function handleResumeWorkflow(threadId) {
      workflowLoading.value = true
      try {
        const data = await workflowApi.getState(threadId)
        currentThreadId.value = threadId
        currentWorkflow.value = mergeWorkflowData(data)
      } catch (error) {
        showToast(t.value.failedToLoad + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    async function handleSelectTopic() {
      if (!selectedTopic.value) return
      workflowLoading.value = true
      // 进入草稿生成阶段，初始化流式内容以实现逐字渲染
      if (currentWorkflow.value) {
        currentWorkflow.value = { ...currentWorkflow.value, status: 'draft_generated', article_content: '' }
      }
      try {
        await workflowApi.streamResume(
          currentThreadId.value,
          'select_topic',
          { selected_topic: selectedTopic.value },
          (token) => {
            if (currentWorkflow.value) currentWorkflow.value.article_content += token
          },
          (data) => {
            if (data && Object.keys(data).length) currentWorkflow.value = mergeWorkflowData(data)
          },
          (error) => {
            showToast(t.value.failed + ': ' + error.message, 'error')
          },
        )
        await loadThreadList()
      } catch (error) {
        showToast(t.value.failed + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    async function handleApprove() {
      workflowLoading.value = true
      try {
        await workflowApi.streamResume(
          currentThreadId.value,
          'approve',
          {},
          (token) => {
            if (currentWorkflow.value) currentWorkflow.value.article_content += token
          },
          (data) => {
            if (data && Object.keys(data).length) currentWorkflow.value = mergeWorkflowData(data)
          },
          (error) => {
            showToast(t.value.failed + ': ' + error.message, 'error')
          },
        )
        await loadThreadList()
      } catch (error) {
        showToast(t.value.failed + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    async function handleReject() {
      workflowLoading.value = true
      showRejectDialog.value = false
      try {
        const data = await workflowApi.reject(currentThreadId.value, rejectFeedback.value)
        currentWorkflow.value = mergeWorkflowData(data)
        rejectFeedback.value = ''
        await loadThreadList()
      } catch (error) {
        showToast(t.value.failed + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    // Merge workflow response values into top-level for template access
    function mergeWorkflowData(data) {
      if (data && data.values) {
        return { ...data, ...data.values }
      }
      return data
    }

    function handleNewWorkflow() {
      currentWorkflow.value = null
      currentThreadId.value = null
      selectedTopic.value = ''
      topicDirection.value = ''
    }

    // Copy
    async function copyArticle(content) {
      if (!content) {
        showToast(t.value.noContent, 'error')
        return
      }
      try {
        await navigator.clipboard.writeText(content)
        showToast(t.value.copied)
      } catch (e) {
        const ta = document.createElement('textarea')
        ta.value = content
        ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px;opacity:0'
        document.body.appendChild(ta)
        ta.focus()
        ta.select()
        try {
          document.execCommand('copy')
          showToast(t.value.copied)
        } catch (e2) {
          showToast(t.value.copyFailed, 'error')
        }
        document.body.removeChild(ta)
      }
    }

    // Format article (simple markdown) - escape HTML first, then apply markdown, then sanitize
    function formatArticle(content) {
      if (!content) return ''
      const html = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>')
      return DOMPurify.sanitize(html)
    }

    function getStatusText(status) {
      return t.value.status[status] || status
    }

    function getStatusBadgeClass(status) {
      if (status === 'completed') return 'badge-success'
      if (status === 'error' || status === 'review_rejected') return 'badge-error'
      if (status === 'topics_generated' || status === 'draft_generated') return 'badge-warning'
      return 'badge-default'
    }

    // Download image as blob
    async function downloadImage(url, filename) {
      try {
        const response = await fetch(url)
        const blob = await response.blob()
        const blobUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = blobUrl
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(blobUrl)
        showToast(t.value.downloadStarted || 'Download started')
      } catch (error) {
        showToast(t.value.downloadFailed, 'error')
      }
    }

    // Refresh topics (regenerate)
    async function handleRefreshTopics() {
      workflowLoading.value = true
      try {
        const data = await workflowApi.refreshTopics(currentThreadId.value)
        currentWorkflow.value = mergeWorkflowData(data)
        selectedTopic.value = ''
      } catch (error) {
        showToast(t.value.failedToRefresh + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    // Refresh images (regenerate)
    async function handleRefreshImages() {
      workflowLoading.value = true
      try {
        const data = await workflowApi.refreshImages(currentThreadId.value)
        currentWorkflow.value = mergeWorkflowData(data)
      } catch (error) {
        showToast(t.value.failedToRefresh + ': ' + error.message, 'error')
      } finally {
        workflowLoading.value = false
      }
    }

    return {
      lang, t, toggleLang,
      isLoggedIn, isLoginMode, authForm, authError, authLoading, handleAuth, handleLogout,
      topicDirection, generateImages, selectedTopic, currentWorkflow, currentThreadId, threadList,
      loadingThreads, startingWorkflow, workflowLoading, editingThreadId, editingName,
      handleStartWorkflow, handleResumeWorkflow, handleSelectTopic, handleApprove, handleReject,
      handleNewWorkflow, startRename, cancelRename, confirmRename, handleDeleteThread,
      showRejectDialog, rejectFeedback,
      showModelConfig, modelConfig, handleModelConfigSave,
      toast, scoreItems,
      copyArticle, formatArticle, getStatusText, getStatusBadgeClass,
      downloadImage, handleRefreshTopics, handleRefreshImages,
    }
  },
}
</script>

<style scoped>
/* ===== Auth ===== */
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
  padding: var(--s-6);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--c-surface);
  border-radius: var(--r-xl);
  padding: var(--s-10);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--c-border-light);
}
.auth-logo {
  width: 48px;
  height: 48px;
  background: var(--c-primary);
  color: #fff;
  border-radius: var(--r-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: var(--s-6);
}
.auth-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: var(--s-1);
}
.auth-subtitle {
  font-size: 14px;
  color: var(--c-text-muted);
  margin-bottom: var(--s-8);
}
.auth-form { margin-bottom: var(--s-6); }
.form-group { margin-bottom: var(--s-5); }
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-secondary);
  margin-bottom: var(--s-2);
}
.form-error {
  color: var(--c-error);
  font-size: 13px;
  margin-bottom: var(--s-4);
}
.auth-submit {
  width: 100%;
  height: 44px;
  font-size: 15px;
}
.auth-switch {
  text-align: center;
  font-size: 14px;
  color: var(--c-text-muted);
}
.auth-lang-toggle {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--s-2);
}
.link-btn {
  background: none;
  border: none;
  color: var(--c-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
}
.link-btn:hover { text-decoration: underline; }

/* ===== Top Bar ===== */
.topbar {
  height: 56px;
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--s-6);
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: var(--s-3); }
.topbar-logo {
  width: 32px;
  height: 32px;
  background: var(--c-primary);
  color: #fff;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.topbar-brand { font-weight: 600; font-size: 15px; color: var(--c-text); }
.topbar-right { display: flex; align-items: center; gap: var(--s-2); }

/* ===== Layout ===== */
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== Sidebar ===== */
.sidebar {
  width: 280px;
  background: var(--c-sidebar);
  border-right: 1px solid var(--c-border);
  padding: var(--s-5);
  overflow-y: auto;
  flex-shrink: 0;
}
.sidebar-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-text-muted);
  margin-bottom: var(--s-4);
}
.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--s-8) 0;
  gap: var(--s-2);
}
.sidebar-empty-icon { font-size: 32px; margin-bottom: var(--s-2); }

.thread-list { display: flex; flex-direction: column; gap: var(--s-1); }
.thread-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--s-3) var(--s-3);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all var(--t-fast);
}
.thread-item:hover { background: rgba(0,0,0,0.04); }
.thread-item.active {
  background: var(--c-surface);
  box-shadow: var(--shadow-xs);
}
.thread-info { flex: 1; min-width: 0; }
.thread-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: var(--s-1);
}
.thread-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--t-fast);
}
.thread-item:hover .thread-actions { opacity: 1; }
.thread-edit-actions { display: flex; gap: 2px; }
.thread-action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 6px;
  font-size: 12px;
  border-radius: var(--r-sm);
  opacity: 0.6;
  transition: all var(--t-fast);
}
.thread-action-btn:hover { opacity: 1; background: rgba(0,0,0,0.06); }
.thread-rename-input {
  flex: 1;
  font-size: 14px;
  padding: var(--s-1) var(--s-2);
  border: 1px solid var(--c-primary);
  border-radius: var(--r-sm);
  outline: none;
  background: var(--c-surface);
  color: var(--c-text);
  font-family: inherit;
}

/* ===== Content ===== */
.content {
  flex: 1;
  overflow-y: auto;
  padding: var(--s-8);
}

/* Empty State */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}
.empty-state-content {
  text-align: center;
  max-width: 480px;
}
.empty-state-icon {
  width: 64px;
  height: 64px;
  background: var(--c-primary-light);
  color: var(--c-primary);
  border-radius: var(--r-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto var(--s-6);
}
.empty-state-content h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: var(--s-2);
}
.empty-state-content p {
  font-size: 15px;
  margin-bottom: var(--s-8);
}
.start-form {
  display: flex;
  gap: var(--s-3);
  max-width: 500px;
  margin: 0 auto;
}
.start-form .input { flex: 1; }
.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  white-space: nowrap;
}
.toggle-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}
.toggle-text {
  font-size: 13px;
  color: var(--c-text-secondary);
}

/* Workflow */
.workflow-content { max-width: 800px; }
.workflow-header {
  margin-bottom: var(--s-8);
  padding-bottom: var(--s-6);
  border-bottom: 1px solid var(--c-border-light);
}
.workflow-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: var(--s-2);
}
.workflow-section { margin-bottom: var(--s-8); }
.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: var(--s-4);
}

/* Topics */
.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--s-3);
  margin-bottom: var(--s-6);
}
.topic-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: var(--s-5);
  cursor: pointer;
  transition: all var(--t-fast);
}
.topic-card:hover {
  border-color: var(--c-primary);
  box-shadow: var(--shadow-sm);
}
.topic-card.selected {
  border-color: var(--c-primary);
  background: var(--c-primary-50);
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}
.topic-index {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-primary);
  margin-bottom: var(--s-2);
}
.topic-text {
  font-size: 14px;
  color: var(--c-text-secondary);
  line-height: 1.5;
}

/* Scores */
.score-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--s-3);
  margin-bottom: var(--s-6);
}
.score-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border-light);
  border-radius: var(--r-md);
  padding: var(--s-4);
}
.score-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--s-2);
}
.score-label { font-size: 13px; color: var(--c-text-muted); }
.score-value { font-size: 13px; font-weight: 600; color: var(--c-text); }
.score-bar {
  height: 6px;
  background: var(--c-border-light);
  border-radius: var(--r-pill);
  overflow: hidden;
}
.score-fill {
  height: 100%;
  background: var(--c-primary);
  border-radius: var(--r-pill);
  transition: width 0.5s ease;
}

/* Article */
.article-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  overflow: hidden;
  margin-bottom: var(--s-6);
}
.article-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: var(--s-2) var(--s-4);
  border-bottom: 1px solid var(--c-border-light);
  background: var(--c-surface-hover);
}
.article-body {
  padding: var(--s-6);
  font-size: 15px;
  line-height: 1.7;
  color: var(--c-text-secondary);
}
.article-body :deep(p) { margin-bottom: var(--s-4); }
.article-body :deep(strong) { color: var(--c-text); font-weight: 600; }

/* Images */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--s-4);
}
.image-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.image-card img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
}
.image-card .btn {
  display: block;
  text-align: center;
  border-top: 1px solid var(--c-border-light);
  border-radius: 0;
}

/* Action Bar */
.action-bar {
  display: flex;
  gap: var(--s-3);
  margin-top: var(--s-6);
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.dialog {
  background: var(--c-surface);
  border-radius: var(--r-xl);
  padding: var(--s-8);
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
}
.dialog-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--s-6);
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--s-3);
  margin-top: var(--s-6);
}
</style>
