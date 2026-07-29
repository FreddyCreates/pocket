# Real Discrete Skills (Not Fake Bundled Scripts)

**Paper ID:** INL-2026-POCKET.REAL.012  

## Principle

Every action is a **named skill** you can call alone:

```http
POST /v1/skills/run
{"skill": "github_one_page"}

POST /v1/skills/run
{"skill": "antigravity_explore"}

POST /v1/skills/run
{"skill": "record_start", "params": {"label": "my-demo"}}
```

Or chain via ARCHON: `focused demo` (record → one GitHub UI → research → Antigravity → GitHub Desktop → hi-world email → stop record → **learn**).

## Recording (your recorder was flaky — we record)

SPECULUM uses ffmpeg `gdigrab` full desktop →  
`~/.pocket/recordings/pocket-focused-demo-*.mp4`

## Learning

Each focused run writes `~/.pocket/learned_skills/learned_*.json`  
so the system accumulates reusable playbooks.

## Platform

All of this is POCKET API / desk / Latin workers — not a one-off chat script.
