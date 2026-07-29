# POCKET Video Studio — From SPECULUM Raws to Viral Marketing Demos

**Paper ID:** INL-2026-POCKET.STUDIO.017  
**Lab:** ItsNotAI Labs / Medina Tech Labs  

## Pipeline

```
SPECULUM record  →  ~/.pocket/recordings/*.mp4
        │
        ▼
  POCKET Studio (/studio)
        │  presets
        ▼
  viral_phone (9:16) · viral_web (16:9) · story_stack · clean_demo · square
        │
        ▼
  ~/.pocket/studio/exports/*.mp4
```

## Presets

| Preset | Aspect | Look |
|--------|--------|------|
| viral_phone | 9:16 | iPhone bezel, hook title, caption, CTA |
| viral_web | 16:9 | Browser chrome, product bar, CTA |
| story_stack | 9:16 | Story beats + CTA |
| clean_demo | 16:9 | Intro bar + brand for decks |
| square_social | 1:1 | Feed square |

## API

```http
GET  /v1/studio
GET  /v1/studio/recordings
GET  /v1/studio/exports
GET  /v1/studio/presets
POST /v1/studio/render   {"source":"…mp4","preset":"viral_phone","title":"POCKET"}
POST /v1/studio/batch    {"source":"…","presets":["viral_phone","viral_web"]}
POST /v1/studio/auto     {}  # polish latest recording into full pack
GET  /v1/studio/file?name=export.mp4
```

UI: `http://127.0.0.1:8787/studio` (auth same as desk).

## Value

Same recordings that prove the host co-pilot become **marketing assets** without leaving the platform.
