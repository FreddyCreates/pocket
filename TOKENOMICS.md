# TOKENOMICS

Practical tokenomics notes for POCKET / POCK.

This is an embedded product economy, not a public token launch. Keep the model simple enough to run on a single operator machine, and only add chain assumptions when they are real.

## 1. Supply

### Current state

- Unit: `POCK`
- Starting grant: `10,000 POCK`
- Ledger model: local, append-only, with `balance`, `lifetime_minted`, `lifetime_burned`, and recent events
- Policy: soft floor allowed; users can keep working even if the balance goes negative

### Practical rule

- Treat POCK as a usage meter, not an investment asset
- Keep the supply understandable from the UI in one glance
- Do not introduce complicated inflation, rebasing, or multiple overlapping balances unless a product need is proven

### If/when a public token exists

- Define a fixed genesis supply or a narrow mint policy before launch
- Separate the internal POCK meter from any public token until legal, product, and custody decisions are settled
- Do not imply that the local ledger is the same thing as an on-chain asset

## 2. Emissions

### Current live sources

- Signup or local grant
- Manual top-up

### Intended future sources

- Earned credits for verified product actions
- Bridge or mint flow only after the public-token path is approved

### Emission guidance

- Prefer rare, auditable mint events over continuous discretionary inflation
- Mint for onboarding, recovery, or controlled product promos
- Avoid rewarding idle holding; reward usage and shipped output
- Keep issuance visible in the ledger so users can understand where supply came from

## 3. Utility sinks

POCK should mostly be spent where the product creates real cost or real value.

### Live sinks

| Action | Cost | Purpose |
|---|---:|---|
| Open session | 5 | Makes parallel tabs feel real |
| Shell job | 2 | Cheap local execution |
| WSL job | 3 | Slightly heavier local execution |
| Ask / plan only | 1 | Low-cost reasoning without execution |
| Grok handoff package | 8 | Research package and plan write-up |
| Grok execution | 40 | Real model usage |
| Codex execution | 50 | Primary heavy sink |
| Claude execution | 45 | Heavy sink if available |
| Research pull | 12 | Bundled research / planning package |
| Local deploy start | 15 | Shipping cost, not browsing cost |

### Sink design rules

- Spend credits on actions users already associate with cost
- Make heavy model runs the dominant sink
- Keep shell and WSL cheap so they stay useful for verify-and-ship loops
- Charge for deploys only when they represent real platform work
- Do not overcharge for navigation or idle UI

## 4. Vesting

### Internal POCK

- No vesting concept is needed for the local credit meter
- POCK is consumed by use, not held as a claim on future value

### If a public token is ever launched

- Keep vesting separate from product credits
- Use clear allocations for team, treasury, ecosystem, and user rewards
- Standard practical schedules:
  - Team: 4 years with 1 year cliff
  - Advisors: 12 to 24 months, no large upfront unlocks
  - Treasury / ecosystem: milestone-based or slow linear release
  - User rewards: short or event-based, but capped

### Vesting rules of thumb

- Avoid a large day-one circulating supply from insider allocations
- Tie unlocks to ongoing contribution or network growth
- Publish one source of truth for cliffs, unlock dates, and treasury controls
- Do not mix vesting language with the local POCK balance display

## 5. Current recommendation

For this product, the practical setup is:

1. Keep POCK as local embedded credits.
2. Use a visible starting grant so the desk feels usable immediately.
3. Burn credits on session opens, model runs, deploys, and research pulls.
4. Keep mints rare and explicit.
5. Only add vesting if a real public token is approved later.

## 6. Short version

POCK should feel like a working budget for agent activity:

- easy to understand
- cheap to start with
- expensive when compute is heavy
- transparent about where credits go
- simple enough to explain to a user without a whitepaper
