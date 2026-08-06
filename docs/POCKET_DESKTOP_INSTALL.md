# POCKET Desktop Install and Release

## User experience

A customer installs POCKET once and then opens it from the Desktop or Start menu like any other application.

The installed package contains:

- Electron shell;
- local host sidecar at `resources/host/pocket-host.exe`;
- local, cloud, Edge, tray, and start-at-login modes;
- cloud-device pairing;
- x64 or ARM64-specific Windows artifacts.

## Local build

```powershell
.\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch auto
```

Both architectures:

```powershell
.\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch both
```

The build packages the Python runtime with PyInstaller and `--collect-all pocket`, runs focused integrity tests, invokes `electron-builder`, copies artifacts into `releases/desktop`, and generates SHA-256 metadata.

## Modes

```text
POCKET.exe                 configured/default mode
POCKET.exe --local         local Electron desk
POCKET.exe --cloud         Cloudflare account
POCKET.exe --edge          local engine + Edge app window
POCKET.exe --background    tray/start-at-login process
```

## Lifecycle safety

- The host listens on loopback, not `0.0.0.0`.
- If port 8787 already serves healthy POCKET, it is reused.
- If another process occupies port 8787, launch fails visibly.
- No taskkill, Stop-Process, port-killing, or blind restart is used by the product lifecycle.
- The sidecar may continue after the UI window closes; later launches reuse it.
