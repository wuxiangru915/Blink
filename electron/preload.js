/**
 * Electron Preload 脚本
 *
 * 在渲染进程中注入安全 API，禁止直接使用 Node.js
 */

const { contextBridge } = require('electron')

// 暴露安全 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  isElectron: true,
  // 获取后端端口（供调试用）
  getBackendUrl: () => `http://127.0.0.1:${process.env.ELECTRON_BACKEND_PORT || 8787}`,
})
