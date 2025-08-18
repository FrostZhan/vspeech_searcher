const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

let backendProcess = null

function startBackend() {
  const backendPath = path.join(__dirname, 'dist', 'vspeech_backend')
  
  // 检查后端可执行文件是否存在
  if (fs.existsSync(backendPath)) {
    console.log('正在启动后端服务...')
    backendProcess = spawn(backendPath, [], {
      stdio: 'inherit'
    })
    
    backendProcess.on('error', (error) => {
      console.error('后端服务启动失败:', error)
    })
    
    backendProcess.on('close', (code) => {
      console.log(`后端服务退出，退出码: ${code}`)
    })
  } else {
    console.log('未找到后端可执行文件，使用开发模式')
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  win.loadFile(path.join(__dirname, 'frontend', 'index.html'))
}

// 处理文件对话框请求
ipcMain.handle('open-file-dialog', async (event) => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: '视频文件', extensions: ['mp4', 'mov', 'avi', 'mkv'] }
    ]
  })
  return result.filePaths
})

app.whenReady().then(() => {
  // 启动后端服务
  // startBackend()
  
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  // 关闭后端进程
  if (backendProcess) {
    backendProcess.kill()
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
