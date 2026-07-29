# POCKET API — quick start (Grok / Codex / Claude)

**Base URL (local):** `http://127.0.0.1:8787`  
**Public (if tunnel up):** see `PUBLIC_URL.txt` or Desktop status  

## 1. Create a key (operator)

Open **http://127.0.0.1:8787/developers** → Sign in → **Create API key**.

Or:

```http
POST /v1/ai/keys
Authorization: Basic …   # operator
{"name":"grok-client","tier":"pro"}
```

Save `sk_pocket_…` once.

## 2. Auth

```http
Authorization: Bearer sk_pocket_…
```

## 3. Discover

```http
GET /v1/ai
GET /v1/api
GET /health
```

## 4. Call

```bash
curl -s http://127.0.0.1:8787/v1/ai/chat \
  -H "Authorization: Bearer sk_pocket_…" \
  -H "Content-Type: application/json" \
  -d '{"agent":"planner","messages":[{"role":"user","content":"Plan a host demo"}]}'
```

```bash
curl -s http://127.0.0.1:8787/v1/vision/page \
  -H "Authorization: Bearer sk_pocket_…"
```

## Surfaces

| Surface | URL |
|---------|-----|
| Developers / keys | `/developers` |
| Desktop app | `/` |
| Studio | `/studio` |
| Full catalog | `/v1/api` |

Desktop keeps the host online. API is for other agents and apps.
