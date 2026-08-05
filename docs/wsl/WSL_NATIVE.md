# Native WSL Agent — first-class Linux hands

## The story (made real)

POCKET runs on **Windows**. Serious build and research work also needs **Linux**.  
Microsoft’s **Windows Subsystem for Linux (WSL)** is already on the machine — so POCKET treats it as a **first-class agent**, not a buried admin shell.

```text
  Phone / Desk UI
        │
        ▼
  POCKET host (Windows)
        │
        ├── Codex / Grok / Novae  → platform + host workspaces
        └── WSL Native Agent     → real Linux distro hands
                │
                ▼
         Debian / Ubuntu (WSL2)
         ~/pocket-wsl/{src,build,notes,proofs}
```

## What “first-class” means

| Capability | Behavior |
|------------|----------|
| Probe | Lists distros, default, online, `uname` |
| Workspace | Ensures `~/pocket-wsl` tree inside distro |
| Modes | `wsl`, `wsl_native`, `linux` |
| NL + shell | `status`, natural language recipes, or `! cmd` / `run: cmd` |
| Safety | Blocks pipe-to-shell, root wipe, fork bombs; soft-danger needs `force:` |
| Security | **Founder/host only** on a shared operator PC |
| API | `GET /v1/wsl`, `POST /v1/wsl/run`, `POST /v1/wsl/ensure` |
| UI | Desk agent button + phone (when host power) |

## Security boundary

- Market seats on **your** public URL do **not** get **your** WSL.  
- Self-host researchers are founders of **their** PC → they get WSL on **their** install.  
- Same isolation story as desktop/shell: host power ≠ product seat.

## Try it

1. Install WSL + Debian or Ubuntu  
2. Open desk → **WSL** agent  
3. Send `status` then `! ls -la` or `run: git status`

## API

```http
GET  /v1/wsl
POST /v1/wsl/ensure
POST /v1/wsl/run   {"prompt":"status"}
```

Engine module: `pocket.wsl_agent`.
