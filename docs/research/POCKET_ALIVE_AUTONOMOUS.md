# How POCKET Stays Alive — Scalable Host Co-Pilot

**Paper ID:** INL-2026-POCKET.ALIVE.011  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Version:** 1.6+

---

## 1. What you are building

A **host co-pilot**: Latin Python workers + optional LLM composers that use the **real desktop interface** the way a human does — same window, scroll, click, maximize, exit — while you watch live.

This is larger than “open a URL.” It is **Copilot for the whole computer**, with skills, a daemon, and vision.

---

## 2. How it works (architecture)

```
You (desk / phone / API)
        │
        ▼
   ARCHON (alpha orchestrator)
        │
   ┌────┴────┬──────────┬───────────┐
   ▼         ▼          ▼           ▼
REPOSITOR  SCRUTATOR  PORTARIUS  CONSILIARIUS …
(skills)   (skills)   (UI)       (Copilot chat)
        │
        ▼
 live_events  +  live_vision (OCULUS frames)
        │
        ▼
 Desk rail: Live actions + Live vision
```

| Layer | Role |
|-------|------|
| **Skills** | Multi-skill packs per worker (not one job) |
| **Daemon** | Persistent queue — push work anytime |
| **UI maneuver** | SendKeys, focus, maximize, Alt+F4 (no process kill) |
| **UI click** | UI Automation — click named buttons/tabs in-window |
| **Vision** | JPEG frames ~1s for you + agents |
| **LLM (SCRIPTOR)** | Language only when needed (tweets, intros) |

---

## 3. Interface-first rules (demo policy)

1. **One GitHub** — open once; scroll and **click tabs in the same window**.  
2. **No Edge massacre** — never `Stop-Process msedge` during user recording.  
3. **Gentle exit** — Alt+F4 on foreground only.  
4. **No competing ffmpeg** when the operator is recording.  
5. **Vision** stays on so agents see the glass.

---

## 4. Autonomy path (scalable)

| Mode | Behavior |
|------|----------|
| **Manual desk** | You type; ARCHON runs skills |
| **API** | `POST /v1/desk` / `POST /v1/skills/run` |
| **Async daemon** | `{"async":true,"worker":"PORTARIUS","skill":"calc_run"}` |
| **Scheduled** | GUPPY / autonomy daily jobs |
| **Vision loop** | Future: agent reads frame → decides next click |

---

## 5. Why it felt “more alive”

- Live action feed (named agents, python vs llm)  
- Live vision (see what workers see)  
- Same-window UI (scroll/click like a user)  
- Worker brains (`~/.pocket/worker_brains/`) store learned app notes  

---

## 6. Commands

```text
interface demo
```

```http
POST /v1/desk
{"prompt": "interface demo"}

GET /v1/live/vision
GET /v1/workers/live
GET /v1/live/events?after=0
```

---

## 7. Claim

POCKET is the production host co-pilot stack for ItsNotAI Labs / Medina Tech Labs: Latin workers, skills, vision, and interface control — scalable toward full autonomy.
