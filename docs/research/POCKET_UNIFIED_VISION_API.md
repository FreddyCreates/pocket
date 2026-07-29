# Unified Vision + Studio + Workers API

**One API for Grok, Codex, Claude, phone, and desk.**

All options hang off the same host surface: `GET /v1/api`.

## Perception (pixels → symbols)

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/api` | Master catalog (this map) |
| `GET /v1/vision/page?max_ui=800&grid=5` | **Full page render** — micro UI + OCR + visual → symbol graph |
| `POST /v1/vision/page` | Same; body `{max_ui, ocr, visual, image, grid}` |
| `GET /v1/vision/understand` | Fused primary modality brief |
| `GET /v1/pixel/text` | Force text (UI + OCR) |
| `GET /v1/vision/stream?after=N` | Real-time understanding frames |
| `POST /v1/vision/stream/start` | Start stream `{interval, max_ui}` |
| `POST /v1/vision/stream/stop` | Stop stream |
| `GET /v1/vision/stream/status` | Stream buffer / seq |
| `GET /v1/vision/find?q=Save` | Search last page symbol graph |
| `POST /v1/vision/find` | Search (optional `refresh:true`) |
| `POST /v1/vision/click` | Click by name |
| `GET /v1/live/vision` | Raw JPEG |

## Skills (same API via orchestrator)

`POST /v1/skills/run` with `skill` ∈:

- `page_render` / `full_page` / `page_symbols`
- `stream_start` / `stream_stop` / `stream_latest`
- `understand` / `pixel_text` / `see_screen`
- studio: `studio_auto` / `viral_pack` / `studio_render`

## Agents / real world

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/orchestrator/chat` | NL → plan → execute |
| `POST /v1/workers/spawn` | Dynamic vision worker |
| `POST /v1/campaigns/run` | Multi-repo campaign |
| `POST /v1/bridge/open` | Live observe/act session |
| `POST /v1/studio/auto` | Viral video pack from recordings |

## Symbol graph

Each page render returns `symbols[]` with:

`id, source (uia|ocr|visual), kind, text, bbox, click {x,y}, automation_id?, class_name?, invokable?`

Plus:

- `page_text` — full markdown dump agents can read end-to-end
- `counts.by_kind` — buttons / links / inputs / ocr_line / region…
- `action_hints` — ready-to-run click / scroll suggestions
- `how_to_use` — client cookbook for Grok / Codex / Claude

Agents use **text + click** — not ad-hoc scripts.

## Stream loop (real-time)

```
POST /v1/vision/stream/start  {"interval": 1.5, "max_ui": 500}
loop:
  GET /v1/vision/stream?after=<last_seq>
  → frames[].brief, page_text_head, symbols_head, action_hints
POST /v1/vision/stream/stop
```

## Auth

`Basic` **or** `X-Pocket-Access` **or** `Bearer sk_pocket_…`
