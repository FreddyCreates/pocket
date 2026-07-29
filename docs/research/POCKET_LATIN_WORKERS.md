# Latin Python Workers & Alphas

**Paper ID:** INL-2026-POCKET.LAT.009  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

## Why Latin

Deep, stable names for multimodal Python workers as the platform integrates more surfaces. **GUPPY** is the exception (kept).

## Alphas

| ID | Meaning | Role |
|----|---------|------|
| **ARCHON** | Chief magistrate | Multimodal desk orchestrator |
| **HYDRA** | Many heads | Parallel multi-job fan-out |
| **GUPPY** | Fish (kept) | Silent commercial multi-step |

## Specialists

| ID | Meaning | Jobs |
|----|---------|------|
| **SCRUTATOR** | Examiner | lookup, research, analyze_repo |
| **SCRIPTOR** | Scribe | LLM compose (tweet/email/intro) |
| **PORTARIUS** | Doorkeeper | open apps, Edge, X |
| **OCULUS** | Eye | screenshot paste-back |
| **SPECULUM** | Looking-glass | **screen record demos** |
| **REPOSITOR** | Storekeeper | git, gh, clone, analyze |
| **CONSILIARIUS** | Advisor | Copilot paste + **send** |
| **TABELLARIUS** | Courier | Outlook **draft** (no send) |
| **NAVIGATOR** | Pilot | browser multi-step |

## Easy API (phone = desktop)

```http
POST /v1/desk
{"prompt": "analyze brain ai"}

POST /v1/desk
{"worker": "CONSILIARIUS", "job": "introduce", "prompt": "Hello from POCKET"}

POST /v1/desk
{"worker": "ARCHON", "job": "demo", "prompt": "open antigravity then screenshot"}

GET /v1/workers
```

## Recorded demos

ARCHON `demo` → SPECULUM starts ffmpeg gdigrab → plan runs → stop →  
`~/.pocket/recordings/pocket-archon-demo-*.mp4`

## Claim

Named workers are product IP of ItsNotAI Labs / Medina Tech Labs.
