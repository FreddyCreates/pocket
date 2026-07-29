# POCKET for users — how it is packaged

You asked: **how do I present this to users?**  
Answer: **two channels**, not a research landing page.

---

## 1. Desktop (primary for you · where Fusion Sense lives)

| | |
|--|--|
| **What** | POCKET Desktop app window on the Windows host |
| **Why** | Fusion Sense, click, record, remake need the real OS |
| **Start** | `Start-POCKET-Desktop.ps1` or `python -m pocket desktop` |
| **UI** | Desk at `http://127.0.0.1:8787/` inside a native/Edge app window |
| **Engines** | perception · RFE · vcomp · missions · studio · agents · NEXUS |

This is the product you sit in front of every day.

---

## 2. Cloud / API (sellable · remote AIs · phone)

| | |
|--|--|
| **What** | Same engines over HTTP |
| **Who** | Grok, Codex, Claude, phone, automations |
| **Start** | Runtime always-on + optional Cloudflare tunnel |
| **Catalog** | `GET /v1/api` |
| **Auth** | `sk_pocket_` · Basic · `X-Pocket-Access` |
| **Public** | `pocket.medinatechlabs.net` when tunnel is up |

API is how other brains use your host. Desktop is how *you* operate the host.

---

## What not to lead with

- Research journals as the app  
- Manifesto-only landing pages  
- Fake “open Notepad” demos as the story  

Lead with: **Desktop open → Full page sense → one real task → product phone remake.**

---

## Commands

```powershell
# Desktop product
.\scripts\Start-POCKET-Desktop.ps1
# or
python -m pocket desktop

# Channels JSON
python -m pocket channels

# API runtime only
.\Start-POCKET.ps1
```

API: `GET /v1/product/channels`
