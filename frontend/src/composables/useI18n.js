import { ref, computed } from 'vue'

const i18n = {
  zh: {
    signIn: '登录', signUp: '注册', signInTo: '登录以继续', createAccount: '创建账号',
    username: '用户名', password: '密码', usernameHint: '至少3个字符', passwordHint: '至少6个字符',
    noAccount: '还没有账号？', hasAccount: '已有账号？',
    signOut: '退出登录', history: '历史记录', noWorkflows: '暂无工作流',
    startCreate: '开始创建内容', startDesc: '输入主题方向，AI 将为你生成选题、撰写文章并生成配图',
    topicPlaceholder: '例如：AI技术、Python编程、前端开发...', generate: '生成',
    selectTopic: '选择选题', selectTopicDesc: 'AI 生成了以下选题，请选择一个继续',
    confirmTopic: '确认选题', articlePreview: '文章预览',
    relevance: '相关性', readability: '可读性', depth: '技术深度', originality: '原创性',
    copy: '复制', approve: '通过', requestChanges: '驳回修改',
    contentReady: '内容完成', generatedVisuals: '生成配图', download: '下载', createNew: '新建内容',
    processing: '处理中...', feedback: '修改意见', feedbackPlaceholder: '请输入修改意见...',
    cancel: '取消', submit: '提交', rename: '重命名', delete: '删除',
    deleteConfirm: '确定要删除此工作流吗？此操作不可撤销。',
    copied: '已复制到剪贴板', copyFailed: '复制失败', noContent: '没有内容可复制',
    renamed: '已重命名', deleted: '已删除', new: '新建', refreshTopics: '换一批', refreshImages: '换一批配图', downloadStarted: '开始下载',
    generateImages: '生成配图',
    untitled: '未命名', contentWorkflow: '内容工作流', downloadFailed: '下载失败', failed: '失败',
    failedToStart: '启动失败', failedToLoad: '加载失败', renameFailed: '重命名失败',
    deleteFailed: '删除失败', failedToRefresh: '刷新失败',
    modelConfig: '模型配置', settings: '设置', custom: '自定义', default: '默认',
    resetDefault: '恢复默认', save: '保存', llmModel: 'LLM 模型', llmModelFast: '快速模型',
    llmTemperature: '温度', imageModel: '图片生成模型', configSaved: '配置已保存',
    configReset: '已恢复默认配置', configCleared: '已清除自定义配置', clearCustom: '清除自定义配置',
    llmBaseUrl: 'LLM Base URL', llmApiKey: 'LLM API Key', imageBaseUrl: '图片 Base URL',
    imageApiKey: '图片 API Key', apiKeyHint: '留空则使用系统默认', showApiKey: '显示密钥', hideApiKey: '隐藏密钥',
    status: { initialized: '已初始化', topics_generated: '待选题', retrieved: '已检索',
      draft_generated: '待审核', evaluated: '已评估', review_approved: '已通过',
      review_rejected: '已驳回', visuals_extracted: '已提取', completed: '已完成', error: '错误' },
  },
  en: {
    signIn: 'Sign in', signUp: 'Sign up', signInTo: 'Sign in to continue', createAccount: 'Create your account',
    username: 'Username', password: 'Password', usernameHint: 'At least 3 characters', passwordHint: 'At least 6 characters',
    noAccount: "Don't have an account?", hasAccount: 'Already have an account?',
    signOut: 'Sign out', history: 'History', noWorkflows: 'No workflows yet',
    startCreate: 'Start creating content', startDesc: 'Enter a topic direction and AI will generate options, write articles, and create visuals.',
    topicPlaceholder: 'e.g. AI technology, Python programming, web development...', generate: 'Generate',
    selectTopic: 'Select a topic', selectTopicDesc: 'AI generated these options. Pick one to continue.',
    confirmTopic: 'Confirm topic', articlePreview: 'Article preview',
    relevance: 'Relevance', readability: 'Readability', depth: 'Depth', originality: 'Originality',
    copy: 'Copy', approve: 'Approve', requestChanges: 'Request changes',
    contentReady: 'Content ready', generatedVisuals: 'Generated visuals', download: 'Download', createNew: 'Create new content',
    processing: 'Processing...', feedback: 'Feedback', feedbackPlaceholder: 'Describe what needs to change...',
    cancel: 'Cancel', submit: 'Submit', rename: 'Rename', delete: 'Delete',
    deleteConfirm: 'Delete this workflow? This cannot be undone.',
    copied: 'Copied to clipboard', copyFailed: 'Copy failed', noContent: 'No content to copy',
    renamed: 'Renamed', deleted: 'Deleted', new: 'New', refreshTopics: 'Refresh', refreshImages: 'Refresh images', downloadStarted: 'Download started',
    generateImages: 'Generate images',
    untitled: 'Untitled', contentWorkflow: 'Content Workflow', downloadFailed: 'Download failed', failed: 'Failed',
    failedToStart: 'Failed to start', failedToLoad: 'Failed to load', renameFailed: 'Rename failed',
    deleteFailed: 'Delete failed', failedToRefresh: 'Failed to refresh',
    modelConfig: 'Model Config', settings: 'Settings', custom: 'Custom', default: 'Default',
    resetDefault: 'Reset', save: 'Save', llmModel: 'LLM Model', llmModelFast: 'Fast Model',
    llmTemperature: 'Temperature', imageModel: 'Image Model', configSaved: 'Configuration saved',
    configReset: 'Reset to default', configCleared: 'Custom configuration cleared', clearCustom: 'Clear custom config',
    llmBaseUrl: 'LLM Base URL', llmApiKey: 'LLM API Key', imageBaseUrl: 'Image Base URL',
    imageApiKey: 'Image API Key', apiKeyHint: 'Leave empty to use system default', showApiKey: 'Show key', hideApiKey: 'Hide key',
    status: { initialized: 'Initialized', topics_generated: 'Topics ready', retrieved: 'Retrieved',
      draft_generated: 'Draft ready', evaluated: 'Evaluated', review_approved: 'Approved',
      review_rejected: 'Rejected', visuals_extracted: 'Visuals ready', completed: 'Completed', error: 'Error' },
  },
}

export function useI18n() {
  const lang = ref(localStorage.getItem('lang') || 'zh')
  const t = computed(() => i18n[lang.value])

  function toggleLang() {
    lang.value = lang.value === 'zh' ? 'en' : 'zh'
    localStorage.setItem('lang', lang.value)
  }

  return { lang, t, toggleLang }
}
