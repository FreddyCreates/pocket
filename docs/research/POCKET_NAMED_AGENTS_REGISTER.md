# Named Agents Register — POCKET Platform

**Paper ID:** INL-2026-POCKET.AGT.008  
**Lab:** ItsNotAI Labs · Medina Tech Labs  

## Orchestration agents (Browser / host)

| ID | Class | Speaks? | Tokens |
|----|-------|---------|--------|
| browser_orchestrator | host | reports | no |
| research_worker | python | no | web only |
| composer | llm (codex/grok) | yes | yes |
| edge_host | python | no | no |
| capture | python | no | no |
| github / repos | python | no | no |
| copilot_intro | python (+ optional llm) | clipboard | optional |
| guppy | python | no | no |
| doer | python | no | no |
| autonomy | python scheduler | no | no |

## Desk session modes

codex · grok · claude · plan · browser · capture · repos · copilot · guppy · doer · desktop · web · nexus · term · shell · wsl · handoff

## Headless sellable agents

See `GET /v1/ai/agents` — includes `browser`, `capture`, `repos`, `copilot_intro`, `guppy`, `doer`, `coder`, …

## CLI partners (inventory)

git · gh · codex · claude · grok · antigravity · cursor · code · node · docker · wrangler · cloudflared · wsl · …

Discovered at runtime via `GET /v1/cli/tools`.
