/**
 * POCKET Electron — attach to running host; only start serve if health fails.
 * Does NOT fight with an already-running host.
 */
const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const http = require("http");
const { spawn } = require("child_process");

const PORT = 8787;
const DESK = `http://127.0.0.1:${PORT}/desk`;
let mainWindow = null;
let hostProc = null;
let quitting = false;

if (app.setName) app.setName("POCKET");
if (process.platform === "win32" && app.setAppUserModelId) {
  app.setAppUserModelId("com.medinatech.pocket");
}

// Single-instance: if another POCKET is alive, focus it. Do not flash-quit
// in a way that looks like "opened and closed" when zombies hold the lock.
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  // Another instance owns the lock — exit quietly (it should raise its window)
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

function root() {
  return process.env.POCKET_ROOT || path.resolve(__dirname, "..");
}

function py() {
  const c = path.join(
    process.env.LOCALAPPDATA || "",
    "Programs",
    "Python",
    "Python311-arm64",
    "python.exe"
  );
  return fs.existsSync(c) ? c : "python";
}

function health() {
  return new Promise((resolve) => {
    const req = http.get(
      { hostname: "127.0.0.1", port: PORT, path: "/health", timeout: 2000 },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200);
      }
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

function ensureHost() {
  return health().then((ok) => {
    if (ok) return true;
    if (hostProc && hostProc.exitCode == null) return wait(40000);
    const r = root();
    hostProc = spawn(
      py(),
      ["-u", "-m", "pocket", "serve", "--host", "127.0.0.1", "--port", String(PORT)],
      {
        cwd: r,
        env: {
          ...process.env,
          PYTHONPATH: path.join(r, "src"),
          POCKET_MESH_HOOK: "0",
          POCKET_ALWAYS_MESH: "0",
          POCKET_HEADLESS_AUTO: "0",
          POCKET_AURO_TRAIN: "0",
        },
        windowsHide: true,
        stdio: "ignore",
      }
    );
    hostProc.on("exit", () => {
      hostProc = null;
    });
    return wait(40000);
  });
}

async function wait(ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (await health()) return true;
    await new Promise((r) => setTimeout(r, 400));
  }
  return health();
}

app.whenReady().then(async () => {
  // Create window immediately so the shell never looks like a flash-close
  // while host health is still starting.
  mainWindow = new BrowserWindow({
    title: "POCKET",
    width: 1360,
    height: 880,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: "#09090b",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  mainWindow.once("ready-to-show", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
  // Never let an unexpected close kill the session silently during load
  mainWindow.on("unresponsive", () => {
    console.error("[POCKET] window unresponsive");
  });
  mainWindow.webContents.on("did-fail-load", (_e, code, desc, url) => {
    console.error("[POCKET] did-fail-load", code, desc, url);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.loadURL(
        "data:text/html," +
          encodeURIComponent(
            `<body style="background:#09090b;color:#fff;font-family:system-ui;padding:40px">
            <h1>POCKET desk failed to load</h1>
            <p>${String(desc || code)}</p>
            <p><a style="color:#10a37f" href="${DESK}">Retry desk</a></p>
            </body>`
          )
      );
    }
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\/127\.0\.0\.1/.test(url) || /^https?:\/\/localhost/.test(url)) {
      return { action: "allow" };
    }
    if (/^https?:/.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });

  // Boot splash while host comes up
  mainWindow.loadURL(
    "data:text/html," +
      encodeURIComponent(
        `<body style="background:#09090b;color:#e4e4e7;font-family:system-ui;padding:48px">
        <h1 style="color:#10a37f;margin:0 0 12px">POCKET</h1>
        <p>Starting host on :8787…</p>
        </body>`
      )
  );
  mainWindow.show();

  const ok = await ensureHost();
  if (ok) {
    mainWindow.loadURL(DESK);
  } else {
    mainWindow.loadURL(
      "data:text/html," +
        encodeURIComponent(
          `<body style="background:#09090b;color:#fff;font-family:system-ui;padding:40px">
          <h1>POCKET host not running</h1>
          <p>Run <b>scripts\\Start-POCKET-NOW.cmd</b> or wait for runtime-worker, then click Retry.</p>
          <p><a style="color:#10a37f" href="${DESK}">Retry desk</a></p>
          </body>`
        )
    );
  }
});

app.on("window-all-closed", () => {
  quitting = true;
  // Do NOT kill host — leave it for browser use
  app.quit();
});

// Keep process alive if last window closed unexpectedly on some Windows builds
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0 && !quitting) {
    app.relaunch();
  }
});
