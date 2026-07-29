# Cost analysis: 20 users on POCKET (analysis only)

**Not a quote.** Order-of-magnitude for planning.

## What you pay today (you, 1 operator)

| Line | Cost |
|------|------|
| Codex / OpenAI agent | Your existing subscription or API |
| Grok Build | Your existing plan |
| PC electricity | Low tens of $/mo |
| POCK credits | **$0** — internal meter only |
| Cloudflare quick tunnel | Free (can be flaky) |

**Idle open sessions** ≈ free externally. **Running** Codex/Grok jobs = real LLM spend.

## Real LLM tokens

POCKET now tracks:

- Parsed `tokens used` lines from Codex logs  
- Estimated tokens for Grok from prompt+output chars when CLI doesn’t report  
- `GET /v1/usage` → `llm_tokens` and `llm_tokens_by_engine`

Terminal output length ≠ billable tokens, but Codex “tokens used” is close to real.

## 20 users — two scenarios (22 workdays)

Assumptions: 60% Codex-class jobs @ ~$0.15 hint, 10% Grok @ ~$0.10, 30% shell free.

| Scenario | Jobs/user/day | Jobs/month | LLM USD hint | POCK burn (internal) |
|----------|---------------|------------|--------------|----------------------|
| Light | 5 | 2,200 | ~$200 | ~high tens of thousands |
| Heavy | 25 | 11,000 | ~$1,000 | much higher |

Plus infra if multi-tenant: VPS $40–200, CF tunnel, **auth + isolation engineering** (main missing piece).

## Honest product note

POCKET today = **powerful single-operator multi-agent platform**.  
20 concurrent *customers* needs: accounts, quotas, per-user keys, process isolation — not just Cloudflare.

## API

`GET /v1/cost/20-users`
