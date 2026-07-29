# POCKET Desktop (Electron) — production

Electron shell for the local POCKET host UI. Dark window, single-instance, secure defaults.

**Version:** 2.0.1 · **App ID:** `com.medinatech.pocket`

## Requirements

- Node.js 18+ and npm
- Python with the POCKET package installable as `python -m pocket`
- Host URL default: **http://127.0.0.1:8787/**

## Production run (recommended)

### Option A — launcher (host + Electron)

From the **pocket-os** repo root:

```powershell
.\scripts\Start-POCKET-Electron.ps1
```

What it does:

1. Checks whether something is listening on port **8787**
2. If not, starts `python -m pocket serve` **minimized** (never opens Notepad / `.ps1` as a document)
3. Runs `npm start` in `desktop-electron/`

### Option B — Electron only (auto-starts host)

```powershell
cd desktop-electron
npm.cmd install
npm.cmd start
# or: node run-electron.js
```

`npm start` runs `node run-electron.js` (never opens `npm.ps1` as a document).

If port 8787 is down, **main.js** spawns:

```text
python -m pocket serve --host 127.0.0.1 --port 8787
```

using `POCKET_ROOT` (or the parent folder `../` next to `desktop-electron`). Host is detached and **not** launched via any `.ps1` file.

### Option C — host already running

```powershell
# terminal 1
cd <pocket-os>
$env:PYTHONPATH = ".\src"
python -m pocket serve --host 127.0.0.1 --port 8787

# terminal 2
cd desktop-electron
npm start
```

## Environment

| Variable         | Default                      | Purpose                                      |
|------------------|------------------------------|----------------------------------------------|
| `POCKET_URL`     | `http://127.0.0.1:8787/`     | URL loaded in the BrowserWindow              |
| `POCKET_ROOT`    | parent of `desktop-electron` | Repo root for `python -m pocket serve`       |
| `POCKET_PYTHON`  | auto-detect / `python`       | Python executable path                       |
| `POCKET_DEV`     | unset                        | Set to `1` to open DevTools                  |

## Security (production defaults)

| Setting              | Value   |
|----------------------|---------|
| `contextIsolation`   | `true`  |
| `nodeIntegration`    | `false` |
| `sandbox`            | `true`  |
| `webSecurity`        | `true`  |

External **http(s)** links open in the system browser only.  
**Never** opens `file://`, `.ps1`, or other script/document paths via `shell` (prevents Notepad dumping script source).

## Package scripts

```bash
npm start          # node run-electron.js
npm run pack       # electron-builder --dir (unpacked; needs electron-builder)
npm run dist       # electron-builder Windows NSIS + portable
npm run dist:arm64 # Windows arm64 packages
npm run dist:x64   # Windows x64 packages
```

### Publish downloadable .exe on the web platform

From **pocket-os** root (recommended):

```powershell
.\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch arm64
# or: -Arch x64 | both
```

This builds packages then runs `python -m pocket desktop-pack`, which copies
artifacts into `releases/desktop/` so the live web app serves them at:

| URL | Purpose |
|-----|---------|
| `/download` | Download page (public) |
| `/download/desktop` | Best Windows .exe (redirect) |
| `/download/files/<name>` | Direct file |
| `/v1/desktop/releases` | JSON catalog |

Public tunnel: `https://pocket.medinatechlabs.net/download`

Do not run a long `electron-builder` build unless you intend to package installers.  
Install builder only when packaging: `npm.cmd install` (pulls `electron-builder` from devDependencies).

## Layout

```text
desktop-electron/
  main.js           # production main process
  preload.js        # minimal contextBridge API
  run-electron.js   # node launcher (avoids npm.ps1 / Notepad)
  package.json      # name: pocket-desktop, productName: POCKET
  scripts/
    Start-POCKET-Electron.ps1  # delegates to repo launcher
  README.md
```

Optional icon (`assets/icon.ico`) is not required; tray uses a minimal built-in image.

## Windows taskbar

`app.setAppUserModelId('com.medinatech.pocket')` so jump lists / notifications group under **POCKET**.
