# POCKET AI API — sellable headless agents

**Product:** multi-agent AI API that runs on the operator host (or your deployment).  
**Meter:** POCK credits + API keys (`sk_pocket_…`).  
**UI optional:** desk is for humans; API is for apps and automation.

## Pricing (list)

| Tier | USD / mo (hint) | Includes |
|------|-----------------|----------|
| Starter | $29 | researcher, planner, writer, data, scout, router |
| Pro | $99 | + coder, grok_coder, reviewer, security, architect, ops, nexus, desktop |
| Enterprise | $299 | + squad, volume keys, multi-seat |

Per-call POCK is on each agent (`GET /v1/ai/agents`).

## Auth

```http
Authorization: Bearer sk_pocket_…
# or
X-API-Key: sk_pocket_…
```

Desk password / session tokens also work for operators.

## Create a key (operator)

```http
POST /v1/ai/keys
{"name":"customer-acme","tier":"pro","monthly_quota":10000}
```

Response includes the secret **once**.

## Catalog (public)

```http
GET /v1/ai
GET /v1/ai/agents
```

## Run a headless agent

```http
POST /v1/ai/agents/researcher/run
Authorization: Bearer sk_pocket_…
Content-Type: application/json

{"task":"research multi-agent desk platforms 2026","sync":true}
```

Async:

```http
POST /v1/ai/jobs
{"agent":"coder","task":"Add version to /health"}

GET /v1/ai/jobs/{job_id}
```

## Chat (OpenAI-shaped subset)

```http
POST /v1/ai/chat
{
  "agent": "planner",
  "messages": [{"role":"user","content":"Plan API key metering"}]
}
```

Use `"agent":"auto"` to route first.

## Route only

```http
POST /v1/ai/route
{"task":"I need a threat model for login"}
```

## Headless agents

| id | Role |
|----|------|
| router | Pick best agent |
| scout | Fast web scan |
| researcher | Deep research |
| planner | Plan only |
| coder | Codex implement |
| grok_coder | Grok implement |
| reviewer | Code review |
| security | Threat model |
| writer | Docs/copy |
| data | Tables/metrics |
| architect | System design |
| ops | Host shell diagnostics |
| nexus_bridge | NEXUS workers |
| desktop_bot | Host apps |
| squad | scout → plan → (coder) |

## Sell motion

1. Deploy POCKET with named tunnel / your domain.  
2. Issue API keys per customer.  
3. Bill subscription seat + overage from POCK burns (`GET /v1/ai/usage`).  
4. Map refill to NEXUS/POCKET subscription.

## Local real verification

```powershell
# catalog
Invoke-RestMethod http://127.0.0.1:8787/v1/ai

# key + run (with desk auth or after create key)
```
