# POCKET Ship Story — From Dead Mailbox to Secured Multi-Agent Platform

**Paper ID:** INL-2026-POCKET.SHIP.001  
**Period:** 2026-07-25 → 2026-07-26  
**Public host:** `https://pocket.medinatechlabs.net/`  
**Authors:** Build session (Grok Build + operator Medina) · Safety path also handed to Codex  

## Abstract

We transformed POCKET from a non-functional “queue/inbox toy” into a **password-protected multi-agent desk** on the operator’s PC, reachable from a phone via a **named Cloudflare tunnel**. The product orchestrates **Codex, Grok, Claude, shell, WSL, live terminals, local deploys, uploads, planning chat, and embedded POCK metering** — without replacing the user’s existing agent CLIs. This paper records what shipped, what failed, how safety was applied, and what the platform is attached to.

## 1. Starting problem

User rejection was correct: early POCKET **looked** like a product but behaved as a dead form (fake replies, no real agent runs, flaky tunnels). Requirements:

1. Real agent execution on the PC  
2. Useful multi-session desk (not one toy function)  
3. Phone access while away  
4. Safety once public  
5. Tokenomics / usage visibility  

## 2. Architecture shipped

| Layer | Implementation |
|-------|----------------|
| HTTP desk | Python `ThreadingHTTPServer` · port **8787** |
| Jobs | Queue → concurrent worker pool → session transcripts |
| Engines | Codex `exec`, Grok `--single --always-approve`, Claude CLI, shell, WSL |
| Streaming | Live `log_tail` + `stream_tokens` while jobs run |
| Terminals | Long-lived PowerShell (PTY-like) |
| Deploys | Static / npm / python with log files |
| Uploads | Zip/files → workspace `uploads/` |
| Organism | Mini **brain** (situational thoughts) + mini **heart** (uptime/bpm) |
| Economy | Embedded **POCK** ledger + cost research |
| Auth | Basic / `X-Pocket-Access` password; `/health` public only |
| Edge | Cloudflare tunnel hostname **pocket.medinatechlabs.net** → `http://127.0.0.1:8787` |
| Always-on | Startup + restart loop when origin dies |

## 3. Safety route (Codex + Grok)

Safety was implemented as a **first-class gate**, not a doc:

1. **Password required** for all `/v1/*` agent/API routes  
2. Credentials on disk: `~/.pocket/ACCESS.txt` + `access.env`  
3. **401** without auth; **429** after repeated failures  
4. Security headers (CSP, frame deny, nosniff, no-store)  
5. Body size cap; shell blocklist for destructive patterns  
6. Zip-slip guard on uploads  
7. Public surface minimized: `/health` + login UI shell  

This design was shared with **Codex** and **Grok** so both coding agents operate **inside** the secured desk (authenticated sessions), not as an open internet shell.

**Honest residual risk:** authenticated users (you) can still run agents that write files and execute tools you approve; safety is **access control + metering + blocklists**, not a sandbox of the entire OS.

## 4. Failures that taught us

| Failure | Cause | Fix |
|---------|-------|-----|
| “Nothing works” | Process dead on 8787 | Always-on / restart loop |
| Bad Gateway 502 | Tunnel up, origin down | Keep POCKET alive |
| Quick tunnel 530 | Flaky trycloudflare | Named host on CF |
| Grok “mailbox” | Wrong product path | Real `grok --single` agent + plan handoff split |
| Auth open after code | Old process not reloaded | Restart with AUTH ON |
| Agent shell thrash | Competing kill/restart scripts | Single durable launcher |

## 5. What POCKET is attached to (your apps)

| Attachment | How |
|------------|-----|
| **Codex CLI** | Sessions mode `codex` · workspace-write |
| **Grok CLI** | Sessions mode `grok` · coding; mode `plan` planning-only |
| **Claude CLI** | If on PATH |
| **Workspaces** | pocket-os, hz-offline, Monad-Hackaton, MESIE, tokenomics, scratch |
| **HZ Hub** | Live probe/connect on suite ports |
| **Local deploys** | Serve or run npm/python apps from workspaces |
| **Phone** | Cloudflare → same desk as PC |
| **POCK / usage** | Burns on session open, jobs, deploys, uploads |

**Value prop:** You keep paying Codex/Grok; POCKET is the **orchestration surface** (parallel sessions, stream, deploy, remote, meter, safety gate).

## 6. Features as of v0.6.2+

- Multi-session: Codex, Grok, Claude, Shell, WSL, Live term, Planning AI, Plan handoff  
- Stream tokens while jobs run  
- Mic **voice → text** (Web Speech API)  
- Scrollable message boxes (compact max-height)  
- Upload zip/files into workspace  
- Tokenomics desk + research docs  
- Platform inventory `GET /v1/platform`  
- Organism brain/heart UI  

## 7. What more we can do next

1. **Cloudflare Access** (email OTP) in front of password  
2. **True PTY** (winpty/xterm.js) for full interactive terminal  
3. **SSE/WebSocket** push instead of poll for streams  
4. **Per-session file drop zone** + drag-and-drop  
5. **Named tunnel service health** alert if origin dies  
6. **Windows Service** for POCKET itself (not only cloudflared)  
7. **Multi-user seats** (only if productized)  
8. **Planning AI** memory across sessions  

## 8. Operator runbook (phone)

1. PC awake + POCKET process running  
2. Open `https://pocket.medinatechlabs.net/`  
3. Login `pocket` / password from `~/.pocket/ACCESS.txt`  
4. Spawn agents; upload files; plan vs code sessions  

## 9. Conclusion

POCKET crossed the line from demo UI to **real remote multi-agent platform** with a **safety gate** suitable for a public hostname, while staying honest: durability depends on the PC staying on, and power users still command strong tools once authenticated. The ship path involved Grok Build orchestration, Codex as peer executor target, and repeated origin/tunnel failure recovery — which is now part of the product (always-on + auth + named tunnel).

---

*End of paper.*
