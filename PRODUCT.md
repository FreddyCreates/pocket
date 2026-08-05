# POCKET v1.5.0 — Product

**Multi-agent desk + GUPPY local fish agent + sellable AI API — production invite seats.**  
Not a demo. Real agents, RBAC, quotas, headless fleet, API keys, desktop (50+ apps), web, NEXUS, phone remote, autonomous daily Python workers.

Full production A→Z: **`docs/PRODUCTION.md`** · Legal: **`docs/LEGAL.md`**

## Start (always)

```powershell
C:\Users\Medin\OneDrive\pocket-os\Start-POCKET.ps1
```

Or:

```powershell
$env:PYTHONPATH="C:\Users\Medin\OneDrive\pocket-os\src;C:\Users\Medin\OneDrive\nexus"
$env:NEXUS_ROOT="C:\Users\Medin\OneDrive\nexus"
python -m pocket runtime
```

Leave runtime running. PC awake. Windows Startup already launches `POCKET-Runtime.cmd`.

| | |
|--|--|
| Local | http://127.0.0.1:8787/ |
| Phone | https://pocket.medinatechlabs.net/ |
| Password | `%USERPROFILE%\.pocket\ACCESS.txt` |
| Doctor | `python -m pocket doctor` (ready 7/7) |

## Product surfaces

| Surface | How |
|---------|-----|
| Codex / Grok / Claude | Agent sessions (real CLIs) |
| Plan | Planning AI (no code writes) |
| Desktop | `list apps` · `open copilot` · `open edge https://…` · multi-step |
| **Browser** | Real world: Edge signed-in · X tweet compose · Win/Web Copilot · Codex/Grok |
| **Capture** | `screenshot` paste-back (no folder) · `snip` tool |
| **Repos** | Folders · zip · git · `gh` · open first 5 GitHub repos |
| **Copilot** | Windows app intro agent (clipboard + open) |
| **Live actions** | Rail shows Python/LLM/host steps as they run |
| **ARCHON + Latin workers** | ARCHON HYDRA SCRUTATOR SCRIPTOR PORTARIUS OCULUS SPECULUM REPOSITOR CONSILIARIUS TABELLARIUS NAVIGATOR (+ GUPPY) |
| **Easy desk API** | `POST /v1/desk` — same power as chat, for phone/desktop clients |
| **GUPPY** | Local fish agent · `lookup …` (open + bring back) · `schedule daily …` |
| Doer | Silent ≤10 steps (Python workers, not LLM tokens) |
| Web | `search …` · `fetch https://…` · `research …` |
| NEXUS | `list` · `run Bridge list_servers` (POCK burn) |
| Terminal | Live PowerShell |
| Upload | Zip/files → workspace/uploads |
| Deploy | Static / npm / python + logs |
| Multi-user | Login + invite register |
| **Headless agents** | 16+ agents via API (incl. guppy, doer) |
| **AI API (sell)** | `sk_pocket_` keys · chat · jobs · metering |
| **Lab papers** | `GET /v1/docs/guppy` · `lab-claims` · `engines-beyond-code` · … |

## Sellable AI API

Docs: `docs/AI_API.md`

| | |
|--|--|
| Catalog | `GET /v1/ai` (public) |
| Agents | `GET /v1/ai/agents` |
| Run | `POST /v1/ai/agents/{id}/run` |
| Chat | `POST /v1/ai/chat` |
| Keys | `POST /v1/ai/keys` |
| List $ | Starter $29 · Pro $99 · Enterprise $299 (hints) |

Headless: `router`, `scout`, `researcher`, `planner`, `coder`, `grok_coder`, `reviewer`, `security`, `writer`, `data`, `architect`, `ops`, `nexus_bridge`, `desktop_bot`, `squad`, `doer`, `guppy`.

Lab: **ItsNotAI Labs / Medina Tech Labs** · Fish agent: **GUPPY**.

## Safety

Auth · multi-user invite · app allowlist · URL policy · shell blocklist · audit log (`~/.pocket/safety.log`) · credit burns.

## Money

POCK burns on agent / NEXUS / web / desktop. Refill = future NEXUS subscription seat. Invite-gated multi-user (not multi-tenant SaaS).

## Real verification

```powershell
powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\real-product.ps1
```

## If public is 502

Origin (this PC :8787) is down. Start runtime again. Cloudflare named tunnel service can stay running; phone only works when POCKET heart is up.
