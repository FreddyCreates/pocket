# AI Workspace — token-saving infrastructure for coding agents

## Why

Every Grok / Codex / Claude / plan turn that re-lists the repo or re-discovers “what are we working on?” **burns tokens**.  
POCKET now maintains a **live AI workspace** that auto-updates as jobs finish and is **injected** into the next prompt.

This is **internal infrastructure**, not a flashy user feature — though the right rail surfaces it.

## Layout

```text
~/.pocket/ai_workspace/{workspace}/
  CONTEXT.md      ← injected each turn (≤ ~2.8k chars)
  SUMMARY.md      ← rolling extractive summary (no LLM)
  INDEX.json      ← shallow tree + mtimes
  RECENT.jsonl    ← last jobs
  STATE.json
  previews/       ← last agent output snippets (right rail)
  sessions/{sid}/ ← per coding-session overlay
```

## Right rail (Antigravity-style)

| Panel | Role |
|-------|------|
| **Session summary** | Always-on rolling summary of this work |
| **Previews** | Agent output + shallow file tree |
| **Agent bus** | Hashed mesh envelopes (`freq-coding`) |
| **Subagents** | Activate with `@` — **not** a chat drop bar |
| Vision / Run / API | Unchanged host tools |

Subagents **remain** in the system. They live on the **right**, not as a drop bar that steals chat space every turn.

## Agent bus (already existed · now wired to coding)

`mesh_disk` identities: `SHA-256(salt || agent_id)`  
Envelopes: **HMAC-SHA256** + optional body cipher  
Artifacts + inbox/outbox under `E:/POCKET_MESH` (or fallback)

Coding agents leave handoff notes on job finish → `freq-coding` + ARCHON notify.

## API

| Method | Path | Use |
|--------|------|-----|
| GET | `/v1/ai-workspace?workspace=parallax&session_id=` | Right rail payload |
| POST | `/v1/ai-workspace/refresh` | Force index rebuild |
| GET | `/v1/agent-bus?channel=freq-coding` | Swarm tail |
| POST | `/v1/agent-bus/send` | Leave hashed note |

## Token pain points → fixes

| Pain | Fix |
|------|-----|
| Recursive tree walk every turn | Shallow INDEX + “do not re-scan” instruction in CONTEXT |
| Re-explaining prior work | SUMMARY.md + session overlay auto-appended |
| Subagent spam in chat | Roster on right rail only; `@` for activate |
| Cross-agent paste walls | Hashed artifacts on mesh bus |
| Research package walls | Grok still gets pull path, but CONTEXT is primary short memory |
| Idle “what do you want” loops | TASK-first prompts + workspace now/goal |

## For agent authors (you)

1. Read injected **AI_WORKSPACE** block first.  
2. Only open files that appear in the tree or were named by the user.  
3. Prefer `leave_artifact` / bus notes for peers over long chat dumps.  
4. Subagents: call when needed via `@NAME` — don’t assume they run every turn.
