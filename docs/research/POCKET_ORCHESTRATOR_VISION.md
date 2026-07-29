# Orchestrator, Workers, Screen Control & Real-Time Vision

**Paper ID:** INL-2026-POCKET.ORCH.013  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

---

## 1. Two paths (solidified)

| Path | What it is | When |
|------|------------|------|
| **Workers (sub-agents)** | Latin workers + skill catalog (100+). Queued, named, learnable. | “Do GitHub / email / record” |
| **Screen control** | PORTARIUS / NAVIGATOR / UI Automation + OCULUS vision | Actually moving the glass |

The **Orchestrator** is the executor. Planning (you / chat / ARCHON / LLM) posts a **plan**; the orchestrator runs skills without the outer model hand-holding every SendKeys.

```
Chat “wow showcase”
   → orchestrator.chat_to_plan()
   → execute_plan(record=True)
        → SPECULUM record
        → each skill → worker action
        → OCULUS frame → vision tape
        → learn skill file
```

---

## 2. Real-time vision while recording

| Feed | Mechanism |
|------|-----------|
| Live frames | `ensure_vision()` ~1s JPEG → `~/.pocket/live/frame.jpg` |
| API | `GET /v1/live/vision` |
| Desk rail | Live vision image |
| Tape while skills run | Each skill samples a frame → `~/.pocket/live/tape/` |
| Full video | SPECULUM ffmpeg gdigrab → `~/.pocket/recordings/*.mp4` |

Yes: agents can **see** the latest frame while the demo records. That is the basis for future “see → click” autonomy.

---

## 3. Skill suite

`GET /v1/skills` — 100+ skills (atomic + playbooks).  
Workers become long-term / short-term / multi-task by **which skills** they own.

---

## 4. Creation engine + simple chat

```http
POST /v1/orchestrator/chat
{"text": "wow showcase fundable"}

POST /v1/workers/create
{"name": "SCOUT", "skills": ["github_one_page", "screenshot", "tweet_hi_world"]}

POST /v1/orchestrator/plan
{"record": true, "steps": [{"skill": "record_start"}, {"skill": "edge_hn"}, {"skill": "record_stop"}]}
```

---

## 5. Virtual computer (next)

Same orchestrator API against a VM/RDP/sandbox host. Skills stay host-agnostic; only the screen transport changes. Codex + Grok can plan; orchestrator still executes.

---

## 6. Purchases & deep UI (roadmap)

With vision + UI Automation + durable skills, checkout flows become teachable playbooks — same architecture, higher risk allowlists.

---

## Claim

The **Orchestrator** is the production execution spine of POCKET: workers as sub-agents, screen as first-class, vision real-time, skills at suite scale.
