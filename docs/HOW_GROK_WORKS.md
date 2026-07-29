# How we got Grok to work in POCKET

## Short answer

POCKET does **not** embed Grok’s brain. It runs the **Grok Build CLI already on your PC** as a headless coding agent:

```text
grok --single "<prompt>" --cwd <workspace> --max-turns 20 --always-approve --output-format plain
```

Phone/UI → HTTP job → worker → that command → stdout streamed back to the session.

---

## What failed at first

| Mistake | Why it failed |
|---------|----------------|
| “Handoff mailbox” only | Wrote `GROK_INBOX.md` and hoped desktop Grok would notice. No agent ran. |
| `grok -p "..."` wrong usage | On this CLI, `-p`/`--single` needs correct flags; bare args mis-parsed. |
| `--permission-mode acceptEdits` only | Headless runs often **would not write files**. |
| OneDrive path issues (Codex) | Separate issue; Grok uses `--cwd` + PATH to `~\.grok\bin`. |

---

## What fixed it

### 1. Use the real CLI binary

```text
C:\Users\Medin\.grok\bin\grok.exe
```

POCKET puts that directory on `PATH` for the child process (`which_grok()` in `grok_bridge.py`).

### 2. Headless single-turn mode

```text
grok --single "<full prompt>"
```

- Prints the reply to stdout and exits (no interactive TUI).
- Suitable for a phone → server → agent pipeline.

### 3. File writes: `--always-approve`

Without this, Grok would *say* it would create a file and exit without writing.

With:

```text
--always-approve
```

we proved real writes (e.g. `GROK_LIVE.txt`).

### 4. Job pipeline

1. UI: session `mode=grok` + message  
2. `POST /v1/sessions/{id}/messages` → job `queued`  
3. Worker claims job → `executor._run_grok_agent` → `grok_bridge.run_grok_exec`  
4. `stream_util.run_streaming` pipes stdout into the session while running  
5. Job `done` → message shows full result  

### 5. Split “plan” from “code”

| Mode | Behavior |
|------|----------|
| **Grok agent** | `run_grok_exec` — real coding agent |
| **Plan handoff** | Research package only → inbox (no agent) |
| **Planning AI** | Grok with `--permission-mode plan` (plan only) |

So the product is not a fake “mailbox” labeled Grok.

### 6. Streaming

`run_streaming` reads process output in chunks and updates `log_tail` / `stream_tokens` on the job so the UI can poll live progress.

---

## Code map

| File | Role |
|------|------|
| `src/pocket/grok_bridge.py` | `which_grok`, `run_grok_exec`, research pull packages |
| `src/pocket/executor.py` | Routes `mode=grok` → Grok agent |
| `src/pocket/stream_util.py` | Live stdout → session |
| `src/pocket/worker.py` | Concurrent job pool |
| `src/pocket/app_ui.py` | **+ Grok** button → session API |

---

## How to verify anytime

```powershell
# CLI alone
$env:Path = "C:\Users\Medin\.grok\bin;" + $env:Path
grok --single "Reply with only: GROK_OK" --max-turns 2 --permission-mode plan --output-format plain

# Via POCKET
# Start runtime, login, open Grok session, send: Create PROOF.txt with one line ok
```

---

## Limits (honest)

- Needs **Grok Build CLI installed and logged in** on the PC.  
- Not the interactive Grok TUI — headless only.  
- PC must be **on** and POCKET runtime running for phone jobs.  
- `--always-approve` is powerful: only expose behind auth (we do).  

---

*This is the path that made Grok a real agent in POCKET, not a handoff toy.*
