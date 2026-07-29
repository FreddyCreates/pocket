# POCKET Embedded Tokenomics (POCK)

**Paper ID:** INL-2026-POCKET.TOK.001  
**Status:** Product-embedded local ledger (pre-chain)  
**Unit:** POCK — platform credits

## Abstract

POCKET meters multi-agent work with an **embedded credit system (POCK)** that lives on the operator machine. Credits burn when users open sessions, run Codex/Claude/Grok/shell/WSL jobs, pull research packages, and deploy local apps. This document specifies sinks, sources, unit economics of open sessions, and the path from local ledger → future public token (design only).

## 1. Why embed tokenomics

1. **Usage loops:** Multi-agent desks generate many concurrent runs; metering makes cost *felt*.
2. **Product truth:** Users see balance + burns beside Live services — not a separate spreadsheet.
3. **Future TGE readiness:** Sinks/sources are already instrumented before any IPO narrative.
4. **Builder psychology:** Credits encourage shipping (deploys, agents) rather than idle tabs alone.

## 2. Unit and ledger

| Field | Meaning |
|-------|---------|
| `balance` | Spendable POCK |
| `lifetime_minted` | Grants + topups |
| `lifetime_burned` | All sinks |
| `events[]` | Append-only local history |

Location: `~/.pocket/tokenomics_ledger.json`  
API: `GET /v1/tokenomics` · `POST /v1/tokenomics/mint`

## 3. Cost table (sinks)

| Action | POCK | Notes |
|--------|------|-------|
| Open session | 5 | Each Codex/Shell/WSL/… tab |
| Shell job | 2 | Local, cheap |
| WSL job | 3 | Local Linux |
| Plan (ask) | 1 | No external model |
| Grok handoff package | 8 | Full research plan write |
| Grok headless exec | 40 | `grok -p` |
| Codex job | 50 | Primary heavy sink |
| Claude job | 45 | If CLI present |
| Research pull | 12 | Bundled in Grok package |
| Local deploy start | 15 | Static HTTP serve |

Starting grant: **10,000 POCK**. Soft floor (debt allowed) so builders are not hard-blocked.

## 4. Open sessions — usage cost research

Let \(N\) = open sessions, \(K\) = concurrent heavy jobs.

- Credits to open: \(5N\)
- If all run Codex once: \(5N + 50K\)
- External USD *hint* (not billing): \(\approx 0.15 \times K\) for Codex-class turns

**Finding:** Session tabs are cheap; **parallel Codex** is the dominant cost both in POCK and external SaaS. Shell/WSL are nearly free — good for deploy/verify loops.

## 5. Sources (mint)

| Source | Status |
|--------|--------|
| Signup/local grant | Live (10k) |
| Manual topup API | Live |
| On-chain bridge / TGE | Design only |
| Earn via deploys / quests | Future |

## 6. Relation to IPO / public token

POCK is **not** a securities offering. It is product telemetry + economy design. A future public token would map sinks (agent compute, deploys, API) to on-chain burns only after legal/product readiness. See also multi-chain design registry in MonadBuilder docs (design, not deploy).

## 7. Implementation map

- `pocket/tokenomics.py` — ledger
- UI rail — balance + recent burns
- Burns wired from sessions, jobs, deploys, Grok pulls

## 8. Conclusion

Embedded POCK makes POCKET a **usage-native multi-agent platform**: open many agents, burn credits, deploy locally, pull research — with transparent cost.
