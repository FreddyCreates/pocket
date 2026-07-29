# First-Class Vision & Dynamic Workers (Not Scripts)

**Paper ID:** INL-2026-POCKET.VIS.014  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

## The problem you called out

Fixed demos that open the same apps are **bootstrap scripts**. They start the system. They are not the product.

The product is:

1. **Vision as a sense** — continuous frames + UI Automation map  
2. **Workers as AIs** — goal → observe → decide → act → memory  
3. **Orchestrator as executor** — you don’t hand-drive every key forever  

## Vision first-class

| API | Role |
|-----|------|
| `GET /v1/live/vision` | Latest JPEG |
| `GET /v1/vision/observe` | Frame + **UI map** + window titles |
| `GET /v1/vision/ui_map` | Clickable name→(x,y) map |
| `POST /v1/vision/click` | Click by name from map |

**Vision → action:** `observe()` → `find_in_map("Issues")` → `click_xy` / `click_by_name`.

Scrolling that felt real is the same family as click-by-name: **interface control**, not link spam.

## Dynamic workers

```http
POST /v1/workers/spawn
{"goal": "explore github page like a user", "name": "SCOUT", "max_steps": 10}
```

Each step: **observe screen → policy decide → act → save brain**.  
Not a canned list of opens. Policy reacts to window titles + UI names.

Brains: `~/.pocket/worker_brains/`.

## Long-running

- `POST /v1/long_workers/start` `{"kind":"always_on"}`  
- `{"kind":"folder_watch"}` — `~/.pocket/watch_inbox`  
- `{"kind":"daily_research"}`  

## VM host

`~/.pocket/host.json` → `{"backend":"remote","base_url":"http://vm:8787"}`  
Same skill/observe API; Codex plans, remote host executes.

## Purchase scaffold

`GET /v1/purchase/playbooks` — **never auto-pay**. Human gate required.

## Chat in UI

Rail **Orchestrator chat** → `POST /v1/orchestrator/chat`.

## Scripts vs workers

| Scripts | Workers |
|---------|---------|
| Fixed order | Goal + loop |
| Demo bootstrap | Long/short lifetime |
| Repeat same opens | React to vision |
| Useful to start | Required to scale |
