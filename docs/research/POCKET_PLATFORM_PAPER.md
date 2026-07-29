# POCKET as a Local Multi-Agent Platform

**Paper ID:** INL-2026-POCKET.PLT.001  
**Thesis:** One operator machine becomes a small PaaS — agents, terminals, deploys, credits, research pulls.

## 1. What you have

| Capability | Surface |
|------------|---------|
| Multi-agent desk | `http://127.0.0.1:8787/` |
| Parallel Codex / Claude / Shell / WSL / Grok | Sessions API + UI |
| Live suite connect | HZ, board, MB, WSL, Codex, cloudflared |
| Embedded tokenomics | POCK ledger |
| Local deploys | Static HTTP apps from any workspace |
| Grok whole-plan pulls | Inbox + `~/.pocket/grok_pulls/` |
| Research corpus | `docs/research/*` |

## 2. Why it’s good (product claims with evidence)

1. **Real execution** — Codex/shell/WSL jobs mutate the PC filesystem (proven E2E).  
2. **Parallelism** — worker pool runs multiple sessions at once.  
3. **Operator visibility** — Live rail + platform manifest = no “is it up?” guessing.  
4. **Economy embedded** — usage is first-class, not an afterthought.  
5. **Deploy loop** — agents build → static deploy → LAN URL — without leaving the desk.  
6. **Grok-native** — every pull is situationally dense (sessions, cost, deploys, plan).

## 3. Workspaces as deploy targets

Workspaces (pocket, hz, monad, mesie, tokenomics, scratch) are not just `cwd`s:

- Codex/Claude edit them  
- Shell/WSL run tools inside them  
- **Deploy** serves them locally (`POST /v1/deploy`)  
- Platform badge: “Powered by POCKET”

## 4. Tooling list (for users & agents)

- Session CRUD + messages  
- Live probe/connect  
- Tokenomics burn/mint  
- Deploy start/stop/list  
- Workspace tools inventory  
- Grok research pull  
- Docs endpoints  

## 5. Security notes

- Bound to operator PC (LAN + optional tunnel)  
- Dangerous shell patterns blocked  
- Deploy roots constrained to workspace  
- No claim of multi-tenant SaaS isolation yet  

## 6. Roadmap (honest)

- Named Cloudflare tunnel  
- Richer deploys (npm/python long-running with log streams)  
- Optional chain bridge for POCK  
- Phone polish parity with desktop  

## 7. Conclusion

POCKET is not a chat toy. It is a **local multi-agent platform** with credits, deploys, and research-grade Grok pulls — the substrate for tokenomics work and shipping.
