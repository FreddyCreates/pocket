# Live Desk Production Guide — Who Does What

**Paper ID:** INL-2026-POCKET.LIVE.007  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Audience:** Operators who just watched X open and a tweet paste in

---

## 1. What you saw (X tweet flow)

| What you saw | Who did it |
|--------------|------------|
| Edge opened | **Python** · `edge_host` |
| Twitter/X compose with text | **Python** · X intent URL + clipboard |
| Tweet text quality | **LLM** · Codex or Grok (`composer`) |
| Research bullets / sources | **Python** · `research_worker` (web search/fetch — not LLM tokens) |
| You clicked **Post** | **You** (human) — POCKET never auto-publishes |

**Was it all Python?** No. Python opened the glass and pasted the draft. The **LLM wrote the words**. The **research** path is deliberately Python so it does not burn coding tokens.

## 2. Named agents (production register)

| Agent ID | Name | Role |
|----------|------|------|
| `browser_orchestrator` | Browser Orchestrator | Intent + step order |
| `research_worker` | Research Worker | Lookup / search / fetch |
| `composer` | Composer | Codex/Grok draft |
| `edge_host` | Edge Host Worker | Signed-in Edge, X, clipboard |
| `capture` | Capture | Screenshot / snip paste-back |
| `repos` / `github` | Repos | Folders, zip, git, `gh` |
| `copilot_intro` | Copilot Intro | Windows Copilot + intro clipboard |
| `guppy` | GUPPY | Multi-step Python fish |
| `doer` | Doer | ≤10 silent steps |
| Live Event Bus | `live_events` | Real-time rail feed |

## 3. Live visibility

- Desk rail: **Live actions** (polls `/v1/live/events`)
- Each open Edge / research / compose / tweet step emits an event
- Roles color: **python** green · **llm** amber · **host** gray

## 4. Signed-in model (passwords stay away)

1. You sign into X / GitHub / Microsoft once in Edge or OS  
2. POCKET launches **Edge Default profile** / `gh` / Windows Copilot  
3. No passwords in POCKET jobs  

## 5. New production utilities

| Surface | Commands |
|---------|----------|
| Capture | `screenshot` (paste-back), `snip` |
| Repos | `open my 5 repos`, `list repos`, `new repo`, `zip`, `github create` |
| Copilot | `introduce`, `open`, `open web` |
| CLI inventory | `GET /v1/cli/tools` (git, gh, codex, claude, grok, antigravity, …) |
| Desktop | Antigravity, screenclip, more apps |

## 6. API

- `GET /v1/live/events?after=N`  
- `GET /v1/cli/tools`  
- `GET /v1/github/repos`  
- Modes: `browser`, `capture`, `repos`, `copilot`  

## 7. Claim

ItsNotAI Labs / Medina Tech Labs claim the **live multi-agent desk** pattern: Python workers for glass + LLM for language + human for publish.

---

*Production documentation — keep this next to the product.*
