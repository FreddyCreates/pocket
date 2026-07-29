# Platform API First — How Everything Must Run

**Paper ID:** INL-2026-POCKET.API.015  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

## The rule

**Nothing important runs as a private shell one-off.**

| Client | Path |
|--------|------|
| POCKET desk UI | `fetch('/v1/…')` |
| Phone | same public URL + auth |
| Grok Build / me | HTTP to platform API |
| Codex | HTTP or headless `sk_pocket_` |
| Future Earth / partners | same API |

If the API cannot do it, the platform cannot do it. Terminal is only for **starting the server**.

## Core entrypoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/platform/capabilities` | What the host co-pilot can do |
| POST | `/v1/orchestrator/chat` | Natural language → plan → execute |
| POST | `/v1/orchestrator/plan` | Explicit skill steps |
| POST | `/v1/skills/run` | One skill |
| POST | `/v1/workers/spawn` | Dynamic vision worker (goal loop) |
| POST | `/v1/campaigns/run` | Multi-repo research + commercial capture |
| GET | `/v1/vision/observe` | First-class vision + UI map |
| GET | `/v1/live/vision` | Live frame |
| POST | `/v1/long_workers/start` | Always-on / folder watch |

Auth: `Authorization: Basic …` or `X-Pocket-Access: <password>` or `Bearer sk_pocket_…`.

## Value vs plain Grok

Grok alone cannot:

- Drive your signed-in Edge / X / GitHub Desktop  
- Record a commercial host demo  
- Spawn vision workers that scroll real UI  
- Run multi-repo campaigns with drafts  
- Persist Latin workers + learned skills on your machine  

That is the fundable wedge: **host co-pilot platform**, not another chat box.

## Scripts vs campaigns

| Scripts | Campaigns / dynamic workers |
|---------|------------------------------|
| Bootstrap | Real work |
| Fixed opens | Goal + observe + act |
| Demo glue | Multi-repo, multi-phase, record |

## Design bar

UI should feel like a product OpenAI/Anthropic would ship: calm dark glass, one orchestrator chat, vision rail, agents as first-class — not a pile of debug buttons (debug stays secondary).
