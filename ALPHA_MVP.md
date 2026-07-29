# POCKET Alpha MVP 2.0.0-alpha

**Production-ready alpha** for operators and agents (Grok / Codex / Claude).

## What this is

A **full host platform**, not scattered scripts:

| Layer | Capability |
|-------|------------|
| **Perception** | Fusion page render (UIA + OCR + visual → 200–900+ symbols) on *every* act path |
| **Virtual computer** | Workspace, multi-terminals, shell, sense/act (Caster / Open-Computer-Use class) |
| **Missions** | Multi-hour queue: step finishes → next prompt (chain work) |
| **Studio** | Real viral presets: `rotato_phone` (letterboxed glass), `x_screencast`, `macbook_web` |
| **Imagine** | Still compositions + fusion remake → HTML + 3D scene |
| **Workflows** | Five multimodal alpha workflows (`wf1`…`wf5`) |

## One API

```
GET  /v1/api
GET  /v1/vcomp
POST /v1/vcomp/open | sense | act | shell | term
POST /v1/missions/start | enqueue | stop
GET  /v1/workflows
POST /v1/workflows/run   { "id": "wf1" }  or  { "all": true }
GET  /v1/vision/page
POST /v1/fusion/remake
POST /v1/studio/render   { "preset": "rotato_phone" }
POST /v1/imagine/compose
```

## Five alpha workflows

1. **wf1** — Fusion sense + remake (symbols → HTML/3D)
2. **wf2** — Open Notepad/Explorer + fusion scroll
3. **wf3** — Edge GitHub + fusion click
4. **wf4** — Virtual computer + terminal + Codex probe + Python file
5. **wf5** — Record → fusion captions → rotato + screencast exports

```powershell
.\scripts\pocket-api.ps1 skill workflow_all
# or
Invoke-RestMethod ... -Method POST -Body '{"all":true}'  # /v1/workflows/run
```

## Multi-hour agent pattern

```json
POST /v1/missions/start
{
  "goal": "Ship research pack",
  "max_hours": 3,
  "queue": [
    {"action": "sense"},
    {"skill": "page_render"},
    {"action": "open_url", "url": "https://github.com"},
    {"action": "scroll", "n": 4},
    {"action": "codex", "command": "codex --version"},
    {"action": "remake"},
    {"action": "studio"}
  ]
}
```

When steps finish, **enqueue** more:

```json
POST /v1/missions/enqueue
{ "id": "m-…", "steps": [ {"action": "sense"}, {"skill": "screenshot"} ] }
```

## Studio craft (fixed)

- **Contain** product UI into phone glass (never cover-crop nonsense)
- Studio gradient + shadow + chassis with transparent glass
- Separate **x_screencast** family (Notion/Figma-style, no fake phone)

## Doctrine

Every new capability updates: **module → HTTP → /v1/api → skill → ~/.pocket persistence**.

Fusion is not a demo — it is the sensory layer for workers, orchestrator, vcomp, and missions.
