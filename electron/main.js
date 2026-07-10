/**
 * Electron 主进程
 *
 * 职责：
 * 1. 启动 Python FastAPI 后端子进程
 * 2. 等待后端健康检查通过
 * 3. 创建 BrowserWindow 加载应用
 * 4. 应用退出时清理子进程
 */

const { app, BrowserWindow, shell } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const http = require('http')
const net = require('net')

// 后端进程引用
let backendProcess = null

// 主窗口引用
let mainWindow = null

// 后端端口（0 = 自动分配空闲端口）
const BACKEND_PORT = 0
let actualPort = 8787

// ─── 工具函数 ──────────────────────────────────────────────

/**
 * 查找可用的 Python 可执行文件
 */
function findPython() {
  const candidates = ['python', 'python3', 'py']
  const { execSync } = require('child_process')
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: 'pipe' })
      return cmd
    } catch {
      // 继续尝试下一个
    }
  }
  return 'python'
}

/**
 * 获取一个空闲端口
 */
function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port
      server.close(() => resolve(port))
    })
  })
}

/**
 * 启动后端子进程
 */
async function startBackend() {
  const pythonCmd = findPython()

  // 判断运行模式：开发模式还是打包模式
  // 开发模式：__dirname 包含项目根目录路径（如 \electron 或 /electron）
  // 打包模式：__dirname 在 Electron 内部 resources/ 目录
  const isDevMode = __dirname.includes(path.sep + 'electron') && !__dirname.includes('node_modules')
  const projectRoot = isDevMode
    ? path.resolve(__dirname, '..')
    : path.join(process.resourcesPath)

  // 确保数据目录存在
  const dataDir = path.join(projectRoot, 'data')
  const logDir = path.join(projectRoot, 'logs')
  try {
    require('fs').mkdirSync(dataDir, { recursive: true })
    require('fs').mkdirSync(logDir, { recursive: true })
  } catch {
    // 目录可能已存在
  }

  // 自动获取空闲端口
  actualPort = await getFreePort()

  console.log(`[Electron] Mode: ${isDevMode ? 'development' : 'packaged'}`)
  console.log(`[Electron] Starting backend on port ${actualPort}...`)
  console.log(`[Electron] Project root: ${projectRoot}`)
  console.log(`[Electron] Python: ${pythonCmd}`)

  // 启动 uvicorn
  backendProcess = spawn(
    pythonCmd,
    [
      '-m', 'uvicorn',
      'app.main:app',
      '--host', '127.0.0.1',
      '--port', String(actualPort),
    ],
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        // Electron 模式下使用 SQLite + MemorySaver
        DATABASE_URL: 'sqlite+aiosqlite:///./data/aicontent.db',
        DEBUG: 'false',
        ELECTRON_BACKEND_PORT: String(actualPort),
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  )

  // 转发后端日志
  backendProcess.stdout.on('data', (data) => {
    const msg = data.toString().trim()
    if (msg) console.log(`[Backend] ${msg}`)
  })

  backendProcess.stderr.on('data', (data) => {
    const msg = data.toString().trim()
    if (msg) console.error(`[Backend] ${msg}`)
  })

  backendProcess.on('error', (err) => {
    console.error(`[Electron] Failed to start backend: ${err.message}`)
  })

  backendProcess.on('exit', (code) => {
    console.log(`[Electron] Backend exited with code ${code}`)
    backendProcess = null
  })

  // 等待健康检查通过
  await waitForHealth(actualPort, 30)
  console.log(`[Electron] Backend is healthy on port ${actualPort}`)
}

/**
 * 轮询健康检查接口
 */
function waitForHealth(port, maxRetries) {
  return new Promise((resolve, reject) => {
    let retries = 0

    function check() {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve()
        } else {
          retry()
        }
        res.resume()
      })

      req.on('error', () => retry())
      req.setTimeout(2000, () => {
        req.destroy()
        retry()
      })
    }

    function retry() {
      retries++
      if (retries >= maxRetries) {
        reject(new Error('Backend health check timeout'))
        return
      }
      setTimeout(check, 1000)
    }

    // 首次延迟 2 秒，给后端启动时间
    setTimeout(check, 2000)
  })
}

/**
 * 终止后端进程
 */
function stopBackend() {
  if (backendProcess) {
    console.log('[Electron] Stopping backend...')
    try {
      // Windows 下用 taskkill 杀进程树
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'])
      } else {
        backendProcess.kill('SIGTERM')
      }
    } catch (e) {
      console.error('[Electron] Error stopping backend:', e)
    }
    backendProcess = null
  }
}

/**
 * 创建主窗口
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    title: 'Blink',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // 加载后端页面
  mainWindow.loadURL(`http://127.0.0.1:${actualPort}/`)

  // 开发模式打开 DevTools
  if (process.env.ELECTRON_DEV === '1') {
    mainWindow.webContents.openDevTools()
  }

  // 外部链接在系统浏览器中打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url)
      return { action: 'deny' }
    }
    return { action: 'allow' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ─── 应用生命周期 ──────────────────────────────────────────

app.whenReady().then(async () => {
  try {
    await startBackend()
    createWindow()
  } catch (err) {
    console.error('[Electron] Startup failed:', err.message)
    const { dialog } = require('electron')
    dialog.showErrorBox(
      '启动失败',
      `后端服务启动失败，请检查 Python 环境和依赖是否正确安装。\n\n错误: ${err.message}`
    )
    app.quit()
  }
})

app.on('window-all-closed', () => {
  stopBackend()
  app.quit()
})

app.on('before-quit', () => {
  stopBackend()
})

// 防止多实例
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}
