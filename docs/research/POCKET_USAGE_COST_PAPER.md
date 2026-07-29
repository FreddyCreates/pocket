# Usage & Cost of Open Multi-Agent Sessions

**Paper ID:** INL-2026-POCKET.COST.001  
**Audience:** Operators running many Codex/Claude/shell/WSL/Grok tabs

## 1. Question

What does it *cost* to keep many sessions open on POCKET, and when does cost spike?

## 2. Cost layers

| Layer | Who bills | When charged |
|-------|-----------|--------------|
| **A. POCK credits** | POCKET local ledger | Open session, each job, deploy, research pull |
| **B. External agent SaaS** | OpenAI Codex / Anthropic / xAI | When that engine actually runs |
| **C. Machine** | You (electricity, CPU, disk) | Always while PC awake |
| **D. Tunnel** | Cloudflare (free quick tunnel limits) | If public URL enabled |

Open **idle** sessions cost little in B/C; they cost small POCK on open and optional idle sampling.

## 3. Measured product behavior

- Worker pool: up to **4 concurrent** jobs.
- Sessions are unlimited tabs; cost scales with **runs**, not merely tab count.
- Parallel Shell A + Shell B + WSL proven; Codex parallel multiplies layer B.

## 4. Worked examples

### Desk: 6 tabs, light use
- 2 Codex idle, 2 Shell, 1 WSL, 1 Grok handoff  
- Open cost: \(6 \times 5 = 30\) POCK  
- One shell command each on 3 terminals: \(+2+2+3 = 7\) POCK  
- **Total ~37 POCK**, ~$0 external

### Desk: 3 Codex shipping feature
- Open: 15 POCK  
- Each completes one coding job: \(3 \times 50 = 150\) POCK  
- USD hint: \(3 \times 0.15 \approx \$0.45\) (order-of-magnitude)  
- **Dominant cost = concurrent Codex**

### Grok full pull
- Research package: 12 POCK  
- Optional `grok -p` exec: +40 POCK + xAI usage  
- Every pull includes whole plan + live/session/deploy research (not a thin ping)

## 5. Optimization guidance

1. Close finished sessions (hygiene; future idle burn).  
2. Prefer Shell/WSL for verify; Codex for edit.  
3. One deploy static server per app, reuse port.  
4. Grok for orchestration/research; Codex for code.  
5. Watch `GET /v1/tokenomics` and usage rail.

## 6. Can Codex start Grok?

Yes, on this machine:

- Grok CLI: `grok -p "…" --cwd …` (headless)  
- POCKET: session `mode=grok` builds research package then runs CLI when present  
- Codex can also `shell` invoke `grok -p` or call POCKET HTTP API  

Codex does **not** drive the interactive Grok TUI; headless is the supported bridge.

## 7. API

- `GET /v1/usage` — run counts + est tokens  
- `GET /v1/tokenomics` — balance, costs, USD hints, session cost estimator  
- `GET /v1/platform` — inventory of what you have  

## 8. Conclusion

**Open sessions are cheap; running many coding agents is not.** POCKET surfaces both POCK and USD hints so multi-agent power stays intentional.
