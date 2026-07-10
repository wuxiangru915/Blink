/**
 * API 服务层
 * 封装所有后端 API 调用
 */

const API_BASE = '/api/v1'

/**
 * 获取存储的 token
 */
function getToken() {
  return localStorage.getItem('token')
}

/**
 * 设置 token
 */
function setToken(token) {
  localStorage.setItem('token', token)
}

/**
 * 清除 token
 */
function clearToken() {
  localStorage.removeItem('token')
}

/**
 * 通用请求方法
 */
async function request(endpoint, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000)
  let response
  try {
    response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') throw new Error('请求超时，请重试')
    throw err
  }
  clearTimeout(timeoutId)

  if (response.status === 401) {
    clearToken()
    window.dispatchEvent(new CustomEvent('unauthorized'))
    throw new Error('认证失败，请重新登录')
  }

  if (!response.ok) {
    let errorDetail = '请求失败'
    try {
      const e = await response.json()
      errorDetail = e.detail || errorDetail
    } catch {
      try {
        const t = await response.text()
        if (t) errorDetail = t
      } catch {}
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

/**
 * SSE 流式请求
 */
async function streamRequest(endpoint, body, onToken, onDone, onError) {
  const token = getToken()
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (response.status === 401) {
    clearToken()
    window.dispatchEvent(new CustomEvent('unauthorized'))
    onError?.(new Error('认证失败，请重新登录'))
    return
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    onError?.(new Error(error.detail || '请求失败'))
    return
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.token) onToken?.(data.token)
          if (data.done) onDone?.(data)
          if (data.error) onError?.(new Error(data.error))
        } catch (e) { /* skip malformed lines */ }
      }
    }
  }
  onDone?.({})
}

/**
 * 认证 API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(username, password) {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    setToken(data.access_token)
    return data
  },

  /**
   * 用户注册
   */
  async register(username, password) {
    const data = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    return data
  },

  /**
   * 获取当前用户信息
   */
  async getMe() {
    return request('/auth/me')
  },

  /**
   * 退出登录
   */
  logout() {
    clearToken()
  },
}

/**
 * 配置 API
 */
export const configApi = {
  /**
   * 获取系统默认模型配置
   */
  async getModels() {
    return request('/config/models')
  },
}

/**
 * 工作流 API
 */
export const workflowApi = {
  /**
   * 启动新工作流
   */
  async start(topicDirection, generateImages = true, modelConfig = null) {
    const body = { topic_direction: topicDirection, generate_images: generateImages }
    if (modelConfig && Object.keys(modelConfig).length > 0) {
      body.model_config = modelConfig
    }
    return request('/workflow/start', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  /**
   * 恢复工作流 - 选择选题
   */
  async selectTopic(threadId, topic) {
    return request(`/workflow/resume/${threadId}`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'select_topic',
        data: { selected_topic: topic },
      }),
    })
  },

  /**
   * 恢复工作流 - 审核通过
   */
  async approve(threadId) {
    return request(`/workflow/resume/${threadId}`, {
      method: 'POST',
      body: JSON.stringify({ action: 'approve' }),
    })
  },

  /**
   * 流式恢复工作流（SSE）
   */
  async streamResume(threadId, action, data, onToken, onDone, onError) {
    return streamRequest(
      `/workflow/stream/resume/${threadId}`,
      { action, data },
      onToken, onDone, onError
    )
  },

  /**
   * 恢复工作流 - 审核驳回
   */
  async reject(threadId, feedback) {
    return request(`/workflow/resume/${threadId}`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'reject',
        data: { feedback },
      }),
    })
  },

  /**
   * 获取工作流状态
   */
  async getState(threadId) {
    return request(`/workflow/state/${threadId}`)
  },

  /**
   * 获取工作流列表
   */
  async list() {
    return request('/workflow/threads')
  },

  /**
   * 重命名工作流线程
   */
  async rename(threadId, name) {
    return request(`/workflow/threads/${threadId}/rename`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    })
  },

  /**
   * 删除工作流线程
   */
  async delete(threadId) {
    return request(`/workflow/threads/${threadId}`, {
      method: 'DELETE',
    })
  },

  /**
   * 换一批选题
   */
  async refreshTopics(threadId) {
    return request(`/workflow/refresh-topics/${threadId}`, {
      method: 'POST',
    })
  },

  /**
   * 换一批配图
   */
  async refreshImages(threadId) {
    return request(`/workflow/refresh-images/${threadId}`, {
      method: 'POST',
    })
  },
}

/**
 * 检查是否已登录
 */
export function isLoggedIn() {
  return !!getToken()
}
