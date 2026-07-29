# POCKET OS: Mobile Operator Substrate for Agent-Native Coding

**Working paper ID:** INL-2026-POCKET.001  
**Authors:** ItsNotAILabs · Alfredo (Freddy) Medina  
**Date:** 2026-07-25  
**Status:** Ship v0.1 · implemented substrate  
**Keywords:** mobile agents, coding orchestration, offline-capable ops, Grok workflow, suite integration  

---

## Abstract

We introduce **POCKET OS** (**POCKET**), a mobile-first operator substrate that lets humans issue coding and suite-control instructions from a phone to a trusted PC agent runtime without requiring an app-store binary. POCKET runs as a local LAN HTTP service, queues structured code intents, optionally mirrors messages into the HZ away-agent pipeline, and surfaces suite “lanes” (SignalLens, NEXUS, MESIE, HZ Hub, Auro-4B, Mini Novas, MonadBuilder+). Unlike generic remote-desktop or chat apps, POCKET is purpose-built as a **coding intake plane**: language tags, durable JSONL queues, terminal watchers, and doctrine-aligned offline operation. We document architecture, threat model, protocol, evaluation of the v0.1 ship, and research agenda.

---

## 1. Introduction

### 1.1 Problem

Operators increasingly direct AI coding agents (Grok, Claude, Cursor, local tools) from desks, but **mobility breaks the loop**:

1. Phone browsers are poor IDEs, yet excellent **intent devices**.  
2. Full remote desktop is heavy, fragile, and over-privileged.  
3. Cloud “mobile coding” products require internet and third-party custody of prompts.  
4. Suite products (mesh chat, research APIs, MCP servers) lack a **single phone front door**.

### 1.2 Contribution

POCKET contributes:

1. A **named product surface** for phone→PC coding orchestration.  
2. A **minimal protocol** (`pocket.code.v1` queue records).  
3. **Integration substrate** with HZ Hub (away mirror, shared doctrine).  
4. A **lane map** so one phone UI routes humans to the full ItsNotAILabs suite.  
5. **Ship-ready** local server (port **8787**) testable on LAN immediately.

### 1.3 Design principles

| Principle | Realization |
|-----------|-------------|
| Local first | HTTP on operator LAN; no mandatory cloud |
| Intent over IDE | Phone sends jobs; PC executes with Grok/tools |
| Durable queues | Append-only JSONL under `~/.pocket/` |
| Compose, don’t silo | Lanes to Signal/Nexus/MESIE/HZ/Auro/Mini Nova |
| Owner control | No silent chain broadcast; operator watches queue |

---

## 2. Related work

| Class | Examples | Gap POCKET fills |
|-------|----------|------------------|
| Remote desktop | Chrome Remote Desktop, RDP | Too heavy; full machine exposure |
| Pair programming | VS Code Live Share | Requires desktop session |
| Chat agents | WhatsApp bots, Telegram bots | Cloud custody; not suite-native |
| BLE mesh chat | BitChat-class | Chat, not coding intake |
| MCP tools | NEXUS, etc. | Desktop-agent side, not phone UX |

POCKET is closest to a **mobile job ticket system** for AI coding, colocated with offline mesh ops.

---

## 3. Architecture

```
┌─────────────┐     LAN HTTP :8787      ┌──────────────────────┐
│  Phone UI   │ ──────────────────────► │  POCKET server (PC)  │
│  (browser)  │ ◄── status / queue ──── │  JSONL code_queue    │
└─────────────┘                         └──────────┬───────────┘
                                                   │ mirror
                                                   ▼
                                        ┌──────────────────────┐
                                        │ HZ away queue        │
                                        │ (~/.hz/away)         │
                                        └──────────┬───────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────┐
                    ▼                              ▼              ▼
             pocket watch                  hz away-watch      Grok/Cursor
             (terminal)                    (terminal AI)      (operator)
```

### 3.1 Components

| Component | Role |
|-----------|------|
| `pocket.server` | Threading HTTP server; UI + API |
| `pocket.watch` | Terminal consumer + optional offline AI plan |
| Mobile HTML | PWA-ish tabs: Code · Lanes · Away · Queue |
| Lane registry | Static map of suite products |

### 3.2 Ports and coexistence

| Port | Service |
|------|---------|
| 8787 | **POCKET** |
| 8765 | HZ Hub |
| 8043 / 5174 | MonadBuilder |
| 5173 | Reserved (other apps) |

---

## 4. Protocol substrate

### 4.1 Code queue record — `pocket.code.v1`

```json
{
  "id": "code-<hex12>",
  "type": "code",
  "from": "Phone",
  "lang": "python|typescript|solidity|rust|auto|refactor|debug",
  "prompt": "…",
  "at": 1785000000.0,
  "status": "queued|answered|cancelled",
  "product": "POCKET"
}
```

Storage: `~/.pocket/code_queue.jsonl` (append-only).

### 4.2 HTTP API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Mobile UI |
| GET | `/health` | Liveness |
| GET | `/v1/status` | Product metadata + LAN URL + lanes |
| POST | `/v1/code` | Enqueue coding intent |
| GET | `/v1/code/queue` | List recent jobs |
| POST | `/v1/away` | Mirror to HZ away agent |
| GET | `/v1/research` | Embedded research paper metadata |

### 4.3 Mirror semantics

On code enqueue, POCKET **best-effort** posts:

```text
[POCKET CODE/<lang>] <prompt prefix>
```

into HZ `away_post`, so a single `hz away-watch` process can observe both freeform away notes and coding tickets.

---

## 5. Security & threat model

| Threat | Mitigation |
|--------|------------|
| LAN attacker posts fake jobs | Bind Private network; future: shared secret / pairing PIN |
| Prompt leakage via cloud | No cloud by default |
| Over-privileged phone | Phone only queues; PC executes |
| Queue growth | Cap reads; operator prune; wipe scripts later |
| Confusion with real Grok app | Branding: *your* platform routing to agents |

**Non-goals v0.1:** public internet exposure without tunnel auth; multi-tenant SaaS.

---

## 6. Evaluation (v0.1 ship)

| Test | Result |
|------|--------|
| Server starts on :8787 | Pass |
| `/health` ok | Pass |
| `/v1/code` enqueues JSONL | Pass |
| Status exposes LAN URL | Pass |
| Lane list non-empty | Pass |
| Mirror to HZ away (if hz importable) | Pass |

### 6.1 Usability hypothesis

Phone-first **intent latency** (time to queue a clear job) should beat remote desktop for “fix this / implement that” microtasks while operator is away from desk.

---

## 7. Research agenda

1. **Pairing PIN** and optional TLS on LAN.  
2. **Streaming agent replies** back to phone UI.  
3. **Mini Nova** assignment: auto-route lang tags to micro-agents.  
4. **Offline BLE intake** when Wi‑Fi absent (compose with HZCHAT).  
5. Empirical study: queue→merge success rate vs IDE remote.

---

## 8. Conclusion

POCKET names and ships a **mobile coding intake substrate** for the ItsNotAILabs suite: local, testable now, integrated with HZ Hub away agents, and designed for Grok-class operators rather than full remote desktops.

---

## References (internal)

- ItsNotAILabs Protocol Suite (`docs/suite/PROTOCOL_SUITE.md`)  
- HZ Hub multi-user + away (`hz-offline/docs/MULTI_USER.md`)  
- Call center lanes (`hz-offline/docs/CALL_CENTER_LANES.md`)  
- Suite architecture research (`docs/suite/RESEARCH_ARCHITECTURE.md`)  
