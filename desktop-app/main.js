const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

// This is the only URL the app actually depends on — the homepage, so it
// opens the same place a browser visit would.
const SITE_URL = 'https://kill3rkai.github.io/F1LeagueRacing/';

// Minimum time the splash stays up, so it doesn't just flash by on a fast
// connection — feels like an intentional launch animation either way.
const MIN_SPLASH_MS = 1500;

function createWindow() {
  const splash = new BrowserWindow({
    width: 360,
    height: 360,
    frame: false,
    resizable: false,
    show: true,
    backgroundColor: '#0d0d0d',
    alwaysOnTop: true,
  });
  splash.loadFile(path.join(__dirname, 'splash.html'));

  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0a0a0a', // matches the site's dark theme — avoids a white flash while it loads
    icon: path.join(__dirname, '../Images/VSM.png'),
    title: 'VSM F1 League',
    show: false,
    webPreferences: {
      // We're only ever loading our own site, but keeping these off is good
      // practice for any BrowserWindow that loads remote content.
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadURL(SITE_URL);

  const startedAt = Date.now();
  win.once('ready-to-show', () => {
    const elapsed = Date.now() - startedAt;
    const remaining = Math.max(0, MIN_SPLASH_MS - elapsed);
    setTimeout(() => {
      if (!splash.isDestroyed()) splash.destroy();
      win.show();
    }, remaining);
  });

  // If the site fails to load (offline, GitHub Pages down, etc.), don't
  // leave the splash spinning forever — show whatever loaded (Chromium's
  // own error page) after the minimum wait instead of hanging.
  win.webContents.on('did-fail-load', () => {
    setTimeout(() => {
      if (!splash.isDestroyed()) splash.destroy();
      win.show();
    }, MIN_SPLASH_MS);
  });

  // No visible menu bar — cleaner, more "app-like" feel matching the site.
  // Reload (Ctrl/Cmd+R) and DevTools (F12) still work, just silently, in
  // case you need them for debugging later — nothing shows up in the UI.
  Menu.setApplicationMenu(null);

  win.webContents.on('before-input-event', (event, input) => {
    const isReload = (input.control || input.meta) && input.key.toLowerCase() === 'r';
    if (isReload) {
      win.reload();
    } else if (input.key === 'F12') {
      win.webContents.toggleDevTools();
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  // macOS convention: re-open a window when the dock icon is clicked and
  // there are no other windows open. Harmless no-op on Windows/Linux.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Standard Electron convention: quit when all windows are closed, except
// on macOS where apps usually stay running in the dock.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});