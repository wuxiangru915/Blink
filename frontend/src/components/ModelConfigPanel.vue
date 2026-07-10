<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')" @keydown.esc="$emit('close')" tabindex="-1">
    <div class="modal-card model-config-panel">
      <div class="modal-header">
        <h2 class="modal-title">{{ t.modelConfig }}</h2>
        <span class="badge" :class="isCustom ? 'badge-warning' : 'badge-success'">
          {{ isCustom ? t.custom : t.default }}
        </span>
        <button class="modal-close" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <!-- LLM 配置区 -->
        <div class="config-section">
          <div class="config-section-title">LLM</div>
          <div class="form-group">
            <label class="form-label">{{ t.llmModel }}</label>
            <input v-model="form.llm_model" type="text" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.llmModelFast }}</label>
            <input v-model="form.llm_model_fast" type="text" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.llmBaseUrl }}</label>
            <input v-model="form.llm_base_url" type="text" class="input" :placeholder="t.apiKeyHint" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.llmApiKey }}</label>
            <div class="password-row">
              <input
                v-model="form.llm_api_key"
                :type="showLlmKey ? 'text' : 'password'"
                class="input"
                :placeholder="t.apiKeyHint"
              />
              <button class="btn btn-ghost btn-sm toggle-btn" @click="showLlmKey = !showLlmKey">
                {{ showLlmKey ? t.hideApiKey : t.showApiKey }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.llmTemperature }}</label>
            <div class="slider-row">
              <input v-model.number="form.llm_temperature" type="range" min="0" max="1" step="0.1" class="slider" />
              <span class="slider-value">{{ form.llm_temperature }}</span>
            </div>
          </div>
        </div>

        <!-- 图片配置区 -->
        <div class="config-section">
          <div class="config-section-title">Image</div>
          <div class="form-group">
            <label class="form-label">{{ t.imageModel }}</label>
            <input v-model="form.image_model" type="text" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.imageBaseUrl }}</label>
            <input v-model="form.image_base_url" type="text" class="input" :placeholder="t.apiKeyHint" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ t.imageApiKey }}</label>
            <div class="password-row">
              <input
                v-model="form.image_api_key"
                :type="showImageKey ? 'text' : 'password'"
                class="input"
                :placeholder="t.apiKeyHint"
              />
              <button class="btn btn-ghost btn-sm toggle-btn" @click="showImageKey = !showImageKey">
                {{ showImageKey ? t.hideApiKey : t.showApiKey }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="isCustom" class="clear-config-row">
          <button class="btn btn-danger btn-sm" @click="handleClear">{{ t.clearCustom }}</button>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" @click="resetToDefault">{{ t.resetDefault }}</button>
        <button class="btn btn-ghost" @click="$emit('close')">{{ t.cancel }}</button>
        <button class="btn btn-primary" @click="handleSave">{{ t.save }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { configApi } from '../api.js'
import { useI18n } from '../composables/useI18n.js'

export default {
  name: 'ModelConfigPanel',
  props: {
    visible: Boolean,
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const { t } = useI18n()

    const defaultConfig = ref(null)
    const hasCustomConfig = ref(!!localStorage.getItem('modelConfig'))
    const showLlmKey = ref(false)
    const showImageKey = ref(false)
    const form = reactive({
      llm_model: '',
      llm_model_fast: '',
      llm_base_url: '',
      llm_api_key: '',
      llm_temperature: 0.7,
      image_model: '',
      image_base_url: '',
      image_api_key: '',
    })

    const isCustom = computed(() => hasCustomConfig.value)

    function applyConfig(config) {
      form.llm_model = config.llm_model ?? ''
      form.llm_model_fast = config.llm_model_fast ?? ''
      form.llm_base_url = config.llm_base_url ?? ''
      form.llm_api_key = config.llm_api_key ?? ''
      form.llm_temperature = config.llm_temperature ?? 0.7
      form.image_model = config.image_model ?? ''
      form.image_base_url = config.image_base_url ?? ''
      form.image_api_key = config.image_api_key ?? ''
    }

    async function loadConfig() {
      hasCustomConfig.value = !!localStorage.getItem('modelConfig')
      const saved = JSON.parse(localStorage.getItem('modelConfig') || 'null')
      if (saved) {
        applyConfig(saved)
      }
      try {
        const data = await configApi.getModels()
        defaultConfig.value = data
        if (!saved) {
          applyConfig(data)
        }
      } catch (error) {
        console.error('Failed to load model config:', error)
      }
    }

    function resetToDefault() {
      if (defaultConfig.value) {
        applyConfig(defaultConfig.value)
      }
    }

    function handleSave() {
      const config = {
        llm_model: form.llm_model,
        llm_model_fast: form.llm_model_fast,
        llm_base_url: form.llm_base_url,
        llm_api_key: form.llm_api_key,
        llm_temperature: form.llm_temperature,
        image_model: form.image_model,
        image_base_url: form.image_base_url,
        image_api_key: form.image_api_key,
      }
      localStorage.setItem('modelConfig', JSON.stringify(config))
      hasCustomConfig.value = true
      emit('save', config)
    }

    function handleClear() {
      localStorage.removeItem('modelConfig')
      hasCustomConfig.value = false
      if (defaultConfig.value) {
        applyConfig(defaultConfig.value)
      }
      emit('save', null)
    }

    function handleEsc(e) {
      if (e.key === 'Escape') {
        emit('close')
      }
    }

    watch(
      () => props.visible,
      (val) => {
        if (val) {
          loadConfig()
          document.addEventListener('keydown', handleEsc)
        } else {
          document.removeEventListener('keydown', handleEsc)
        }
      }
    )

    return {
      t, form, isCustom, showLlmKey, showImageKey,
      resetToDefault, handleSave, handleClear,
    }
  },
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-card {
  background: var(--c-surface);
  border-radius: var(--r-xl);
  width: 100%;
  max-width: 520px;
  box-shadow: var(--shadow-lg);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  padding: var(--s-6);
  border-bottom: 1px solid var(--c-border-light);
}
.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--c-text);
  flex: 1;
}
.modal-close {
  background: none;
  border: none;
  font-size: 22px;
  color: var(--c-text-muted);
  cursor: pointer;
  padding: 0 var(--s-1);
  line-height: 1;
  transition: color var(--t-fast);
}
.modal-close:hover {
  color: var(--c-text);
}
.modal-body {
  padding: var(--s-6);
  overflow-y: auto;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--s-3);
  padding: var(--s-6);
  border-top: 1px solid var(--c-border-light);
}
.config-section {
  margin-bottom: var(--s-5);
}
.config-section:last-of-type {
  margin-bottom: 0;
}
.config-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--s-3);
  padding-bottom: var(--s-2);
  border-bottom: 1px solid var(--c-border-light);
}
.slider-row {
  display: flex;
  align-items: center;
  gap: var(--s-3);
}
.slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--c-border-light);
  border-radius: var(--r-pill);
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--c-primary);
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: var(--shadow-sm);
}
.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--c-primary);
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: var(--shadow-sm);
}
.slider-value {
  min-width: 36px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}
.password-row {
  display: flex;
  gap: var(--s-2);
}
.password-row .input {
  flex: 1;
}
.toggle-btn {
  white-space: nowrap;
  font-size: 12px;
}
.clear-config-row {
  margin-top: var(--s-4);
  padding-top: var(--s-4);
  border-top: 1px solid var(--c-border-light);
}
</style>
