const { app, BrowserWindow, globalShortcut, ipcMain, screen } = require('electron');
const path = require('path');
const url = require('url');

// Keep a global reference of the window object to prevent garbage collection
let mainWindow = null;

// Create the browser window
function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  
  mainWindow = new BrowserWindow({
    width: Math.round(width * 0.6), // 60% of screen width
    height: 400,
    frame: false,
    transparent: true,
    resizable: false,
    show: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the index.html of the app
  mainWindow.loadURL(url.format({
    pathname: path.join(__dirname, 'index.html'),
    protocol: 'file:',
    slashes: true
  }));

  // Position the window in the center of the screen
  mainWindow.on('ready-to-show', () => {
    const windowBounds = mainWindow.getBounds();
    mainWindow.setPosition(
      Math.round((width - windowBounds.width) / 2),
      Math.round((height - windowBounds.height) / 3) // Position at 1/3 from top
    );
  });

  // Hide window when it loses focus
  mainWindow.on('blur', () => {
    mainWindow.hide();
  });

  // Emitted when the window is closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Register global shortcut when Electron is ready
app.whenReady().then(() => {
  // Register Cmd+Shift+Space shortcut
  const shortcutRegistered = globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (mainWindow === null) {
      createWindow();
    }
    
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.webContents.send('focus-search');
    }
  });

  if (!shortcutRegistered) {
    console.error('Shortcut registration failed');
  }

  // Create the window if it doesn't exist yet
  if (mainWindow === null) {
    createWindow();
  }
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  // On macOS applications keep their menu bar active until the user quits
  // explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open
  if (mainWindow === null) {
    createWindow();
  }
});

// Unregister all shortcuts when app is about to quit
app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// IPC handlers for renderer communication
ipcMain.on('hide-window', () => {
  if (mainWindow) {
    mainWindow.hide();
  }
});

ipcMain.on('quit-app', () => {
  app.quit();
});
