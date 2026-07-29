# Desktop Autonomy on the Operator Host: Multi-Step Python Workers and Scheduled Fetch

**Paper ID:** INL-2026-POCKET.DESK.002  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Systems:** POCKET · GUPPY · step_agent · autonomy · desktop allowlist  
**Status:** Production-embedded  

---

## Abstract

This paper specifies **desktop autonomy** for POCKET: a design where Python workers—not chat loops—drive multi-step interaction with the host GUI surface (apps, browser, Copilot) and with the public web. We raise the silent step budget to **ten**, introduce **lookup** (open host UI + return fetched evidence), and ship a **schedule daemon** for daily/hourly autonomous runs. The contribution is a zero-LLM-token path for repetitive operator work on a real Windows desk.

## 1. Problem

Human operators repeat:

1. Open browser → search → skim  
2. Open Explorer / notes / calc  
3. “Remind me every morning”  

Classic agent stacks solve this by calling LLMs every cycle. That is wrong for cost and reliability. **Desktop autonomy** treats the OS and HTTP as first-class actuators with an ordered plan.

## 2. Model

A **plan** is an ordered list of steps \(s_1 \ldots s_k\), \(k \le 10\).

Each step is one of:

| Kind | Example | Effector |
|------|---------|----------|
| desktop open | `open explorer` | `desktop.open_app` |
| desktop + URL | `open edge https://…` | Edge launch + navigate (2 internal actions) |
| lookup | `lookup X` | Edge/Copilot open + `web_research.search_web` + optional fetch |
| web | `research X` | Python research job |
| schedule | `schedule daily …` | autonomy store + runner |
| shell (admin) | `shell git status` | allowlisted shell |

Failure policy: stop on hard fail; report ok/fail per step (no user Q&A).

## 3. Lookup: open and bring back

**Claim:** “Open Copilot and look it up” is incomplete unless results return to the desk transcript.

Lookup therefore does **both**:

1. **Host UI** — Edge Bing `showconv=1` + `ms-copilot:` when present  
2. **Python evidence** — DuckDuckGo Instant Answer + Wikipedia-style open search + deep fetch of first URL  

The human sees the same glass surface; POCKET stores the text for agents, phone remote, and GROK_INBOX.

## 4. Scheduling

Schedules live in `~/.pocket/schedules.json`.

| Field | Meaning |
|-------|---------|
| interval | minute / hourly / daily / every_6h / weekly |
| prompt | multi-step or lookup text |
| next_run_at | wall clock |
| last_result_path | `~/.pocket/autonomy_inbox/…` |

Runner: daemon thread started with POCKET embedded worker. **Does not** require Codex/Grok tokens.

## 5. App surface (claimed inventory)

- **Native / Microsoft (20+):** Explorer, Edge, Copilot, Teams, Office, Settings, Task Manager, …  
- **Third-party / AI (20+):** Chrome, Cursor, Discord, ChatGPT, Claude, Grok app, Notion, Docker, …  

Allowlist is the security boundary.

## 6. Relation to coding agents

Desktop autonomy does **not** replace Codex. It **feeds** coding agents: scheduled research deposits markdown that Grok/Codex can later consume in a resumable session.

## 7. Conclusion

POCKET’s desktop autonomy is a lab-grade claim: **Python workers own the glass**, up to ten steps, with scheduled fetch—named engines, named paths, commercial seat ready.

---

*ItsNotAI Labs / Medina Tech Labs*
