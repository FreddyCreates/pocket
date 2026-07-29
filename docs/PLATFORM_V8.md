# POCKET v0.8 — AI for the whole computer

## Not just coding

| Mode | What it does |
|------|----------------|
| Codex / Grok / Claude | Code agents (your CLIs) |
| Plan | Planning AI chat |
| Desktop | Open allowlisted apps (Notepad, Edge, VS Code, Cursor, Office…) |
| Web | Search + fetch + research pages back to the desk |
| NEXUS | MERIDIAN workers (GitHub, drafts, security, ML, federation catalog) |
| Terminal / Shell / WSL | Local execution |
| Deploy | Static / npm / python |

## Safety (real)

- Password + multi-user tokens  
- App **allowlist only** (no arbitrary .exe)  
- Path open limited to home / OneDrive / Documents / .pocket  
- Web: http(s) only, blocked schemes, size cap  
- Shell blocklist  
- Audit log `~/.pocket/safety.log`  
- Credits burn on NEXUS / web / desktop actions  

## NEXUS monetization hook

- NEXUS tools burn **POCK** (and can map to a **NEXUS subscription** refill later)  
- Scribe drafts still **never auto-publish** (NEXUS product rule)  
- Bridge lists external MCP worlds (Tavily, Slack, Linear, …) as catalog; real calls need their keys  

## 10 desktop apps (allowlist)

notepad, explorer, calc, paint, cmd, powershell, wt, code, cursor, chrome, edge, word, excel, snip

## Web

```
search <query>
fetch https://...
research <query>
```

## NEXUS

```
list
run Bridge list_servers
run Archon list_repos {}
```

## Promote

Self-host desk + invite multi-user; charge for NEXUS credit packs / hosted seats later. See PROMOTE.md.
