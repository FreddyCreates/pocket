# POCKET v0.6 — orchestration on top of your CLIs

You already have **Codex** and **Grok**. POCKET does not replace them — it **orchestrates** them.

## Open

**http://127.0.0.1:8787/** (Ctrl+F5)

## Why POCKET is valuable

| You already have | POCKET adds |
|------------------|-------------|
| Codex CLI | Parallel multi-session desk + history |
| Grok CLI | Same + plan handoffs + research pulls |
| Local shell | **Live interactive terminals** (long-lived) |
| Manual deploys | **Static / npm / python** with **logs** |
| Guessing cost | Stream tokens + POCK meter + usage API |
| Desk-only | Phone/LAN remote of the same desk |

## Features (v0.6)

1. **Stream tokens while jobs run** — log + ~tok update every ~0.8s  
2. **+ Live term** — interactive PowerShell (not one-shot)  
3. **Deploy** — Static · **npm** · **python** (+ log button)  
4. **+ Grok agent** / **+ Codex** — your CLIs, multi-tab  
5. **+ Plan handoff** — deferred plans, not coding  

## API highlights

- `GET /v1/platform` — why POCKET + inventory  
- `POST /v1/deploy` `{kind:static|npm|python, workspace, command?}`  
- `GET /v1/deploys/{id}/log`  
- `POST /v1/terminals` · `POST /v1/terminals/{id}/send`  
- Running jobs: `log_tail`, `stream_tokens` on session messages  

## Phone

Same Wi‑Fi: `http://192.168.12.127:8787/`  
Keep PC awake. Startup: `scripts\Start-POCKET-NoAdmin.ps1`
