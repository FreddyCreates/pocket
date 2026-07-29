# Skills, Live Link & Latin Worker Daemon

**Paper ID:** INL-2026-POCKET.SKL.010  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

## Live link

Python Latin workers are **major models** on the host:

- **Daemon** (`worker_daemon`) — persistent background queue  
- **Live state** — `GET /v1/workers/live` (status, skills, runs)  
- **Skills** — multi-skill packs per worker (`skills_registry`)  
- **UI maneuver** — SendKeys / focus / packaged apps (interface, not only URL)  

## Grand demo skill

`ARCHON` → `grand demo` / `POST /v1/desk {"prompt":"grand demo"}`

Order: GitHub×5 → last repo all tabs + research → tweet + email draft → SpaceX → Cursor/Antigravity/Copilot chat → Notepad → Explorer file → Calc → PowerShell → close Edge → TradingView web+app + MetaTrader. SPECULUM records.

## API

```http
GET  /v1/workers
GET  /v1/workers/live
POST /v1/skills/run  {"skill":"copilot_chat_send","prompt":"…"}
POST /v1/desk        {"prompt":"grand demo"}
POST /v1/desk        {"async":true,"worker":"PORTARIUS","skill":"calc_run"}
```
