/**
 * Electron 启动前的准备脚本
 *
 * dev   - 构建前端 → 复制到 static/dist → 启动 Electron（开发模式）
 * start - 构建前端 → 复制到 static/dist → 启动 Electron（生产模式）
 * fast  - 跳过构建，直接启动 Electron（需要 static/dist 已存在）
 * build - 仅构建前端，不启动 Electron
 */

const { spawn } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')

function log(msg) {
  console.log(`[Script] ${msg}`)
}

/**
 * 异步构建前端
 */
function buildFrontend() {
  return new Promise((resolve, reject) => {
    log('Building frontend...')
    const child = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'build'], {
      cwd: path.join(ROOT, 'frontend'),
      stdio: 'inherit',
    })
    child.on('exit', (code) => {
      if (code === 0) {
        log('Frontend build complete.')
        resolve()
      } else {
        reject(new Error(`Frontend build failed with code ${code}`))
      }
    })
    child.on('error', reject)
  })
}

/**
 * 复制 frontend/dist → static/dist
 */
function copyDistToStatic() {
  const src = path.join(ROOT, 'frontend', 'dist')
  const dst = path.join(ROOT, 'static', 'dist')

  if (!fs.existsSync(src)) {
    log('Warning: frontend/dist not found, skipping copy.')
    return
  }

  // 清空目标目录
  if (fs.existsSync(dst)) {
    fs.rmSync(dst, { recursive: true, force: true })
  }
  fs.mkdirSync(dst, { recursive: true })

  // 递归复制
  function copyDir(s, d) {
    const entries = fs.readdirSync(s, { withFileTypes: true })
    for (const entry of entries) {
      const srcPath = path.join(s, entry.name)
      const dstPath = path.join(d, entry.name)
      if (entry.isDirectory()) {
        fs.mkdirSync(dstPath, { recursive: true })
        copyDir(srcPath, dstPath)
      } else {
        fs.copyFileSync(srcPath, dstPath)
      }
    }
  }

  copyDir(src, dst)
  log('Copied frontend/dist -> static/dist')
}

/**
 * 启动 Electron
 */
function startElectron(dev = false) {
  const electronDir = path.join(ROOT, 'electron')
  const env = { ...process.env }
  if (dev) env.ELECTRON_DEV = '1'

  const cmd = process.platform === 'win32' ? 'npx.cmd' : 'npx'
  const child = spawn(cmd, ['electron', '.'], {
    cwd: electronDir,
    env,
    stdio: 'inherit',
  })

  child.on('exit', (code) => {
    log(`Electron exited with code ${code}`)
    process.exit(code || 0)
  })
}

// ─── 主逻辑 ──────────────────────────────────────

async function main() {
  const mode = process.argv[2] || 'dev'

  if (mode === 'dev' || mode === 'start') {
    await buildFrontend()
    copyDistToStatic()
    startElectron(mode === 'dev')
  } else if (mode === 'fast') {
    if (!fs.existsSync(path.join(ROOT, 'static', 'dist', 'index.html'))) {
      log('static/dist not found, building first...')
      await buildFrontend()
      copyDistToStatic()
    }
    startElectron(true)
  } else if (mode === 'build') {
    await buildFrontend()
    copyDistToStatic()
    log('Build complete. Run "npm start" to launch Electron.')
  } else {
    console.log('Usage: node electron/scripts/start.js [dev|start|fast|build]')
    console.log('  dev   - Build frontend + start Electron in dev mode (default)')
    console.log('  start - Build frontend + start Electron in production mode')
    console.log('  fast  - Start Electron without rebuilding (if static/dist exists)')
    console.log('  build - Build frontend only, do not start Electron')
  }
}

main().catch((err) => {
  console.error('[Script] Error:', err.message)
  process.exit(1)
})
