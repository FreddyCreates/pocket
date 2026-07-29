# GUPPY: A Local Commercial Desk Agent for Operator Hosts

**Paper ID:** INL-2026-POCKET.GUPPY.001  
**Authors / Lab:** ItsNotAI Labs · Medina Tech Labs  
**Product family:** POCKET Multi-Agent Platform  
**Status:** Implemented (v1.3.0+)  
**Classification:** Systems paper — product-embedded agent

---

## Abstract

We introduce **GUPPY**, a local commercial desk agent that lives on the operator’s machine and executes multi-step desktop and web work through **Python workers** rather than continuous LLM token streams. GUPPY can open allowlisted host applications (including Microsoft Copilot), navigate the internet via Edge, run up to **ten** silent steps, **look up** topics by opening host UI *and* returning Python-fetched search text, and run **autonomous scheduled** jobs (daily / hourly) that deposit results into a local inbox. The agent is deliberately named and productized: a small fish that swims the desk. This paper claims GUPPY as an ItsNotAI Labs / Medina Tech Labs engine within POCKET.

## 1. Motivation

Cloud chat agents answer questions. Operators need something that **opens Explorer, Edge, Copilot, Cursor** and returns evidence. LLM coding CLIs (Codex, Grok, Claude) are excellent for code; they are expensive and chatty for “open this, look that up, every morning.” GUPPY fills the gap:

| Need | LLM session | GUPPY Python path |
|------|-------------|-------------------|
| Open app | Possible via tool, costly | Allowlist launch, near-zero cost |
| Look up + bring text back | Tokens | Open Bing/Copilot + DuckDuckGo/Wikipedia fetch |
| Daily brief | Human re-prompts | Schedule + background runner |
| Multi-step desk walk | Fragile | Up to 10 ordered steps |

## 2. Architecture

```
Phone / browser desk  →  POCKET session mode=guppy
                              │
                              ▼
                        guppy.run_guppy()
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
        step_agent       web_research     autonomy schedules
        (≤10 steps)      (search/fetch)   (daemon thread)
              │               │                │
              ▼               ▼                ▼
         desktop.open_*   public HTTP     ~/.pocket/autonomy_inbox
         (allowlist)      (no LLM keys)
```

**Engines named in this claim**

| Engine ID | Role |
|-----------|------|
| `guppy` | Commercial local fish agent surface |
| `agent` / `doer` | Silent multi-step executor |
| `desktop` | Allowlisted Windows app control |
| `web` | Search / fetch / research |
| `autonomy` | Scheduled Python worker runner |
| `codex` / `grok` / `claude` | Coding/plan CLIs (separate path; session-resumable) |

## 3. Capabilities (normative)

1. **Identity** — `help` returns lab/company claim + capability list.  
2. **Open** — `open <app>` for 50+ allowlisted native + third-party apps including **Copilot**.  
3. **Lookup** — `lookup <query>` opens Edge (Bing showconv) + Copilot protocol when available, **and** returns structured Python search results + optional deep fetch of first URL.  
4. **Multi-step** — connectors `then` / numbered lists; cap **10**.  
5. **Schedule** — `schedule daily lookup …` · `schedule list` · `schedule cancel <id>`.  
6. **No chat obligation** — Guppy does not ask clarifying questions mid-run.

## 4. Token economy (important claim)

The **worker path does not consume LLM coding tokens**. It uses:

- OS process launch for apps  
- HTTP fetch for web text  
- POCK micro-burns only for metering desk opens/shell-class events  

LLM engines remain available when the operator *wants* code or deep planning; GUPPY is the cheap co-pilot for the glass.

## 5. Commercial seat story

GUPPY is sellable as:

- Headless agent `POST /v1/ai/agents/guppy/run`  
- Desk mode **+ Guppy**  
- API `POST /v1/guppy/run` · catalog `GET /v1/guppy`  

Positioning: **local commercial instance on the customer host**, invite seat, not multi-tenant cloud SaaS.

## 6. Safety

- App allowlist only  
- URL policy (http/https)  
- Shell blocklist for step-shell  
- Schedules run only configured prompts  
- Audit log under `~/.pocket/safety.log`

## 7. Evaluation (product evidence)

| Test | Expected |
|------|----------|
| `lookup multi-agent platforms` | UI opens + brief returned |
| `open edge https://example.com then open notepad` | Both apps |
| `schedule daily lookup AI news` | Schedule id; runner alive |
| Session parallel with Codex | Independent; Guppy not steals Codex thread |

## 8. Related systems (named)

POCKET, POCK ledger, NEXUS MERIDIAN workers, Codex session-resume, Live suite rail — all claimed as Medina Tech Labs / ItsNotAI Labs stack components in sibling papers.

## 9. Conclusion

**GUPPY is the fish.** It is the named, commercial, local desk agent for POCKET: opens the computer you already own, looks things up, brings text home, and can do it on a clock—without burning coding-agent tokens for every click.

---

*© ItsNotAI Labs / Medina Tech Labs. Product-embedded research.*
