# POCKET

**Multi-agent host co-pilot** — real Codex / Grok / Claude / desk agents on *your* machine.  
Phone remote · sellable AI API · Edge desktop app · paper/testnet-first when driving PARALLAX.

Lab: **ItsNotAI Labs / Medina Tech Labs**

## Get POCKET

| Who | How |
|-----|-----|
| **Windows users** | Download the desktop app: [releases](https://github.com/FreddyCreates/pocket/releases) or host `/download` |
| **Operators (this host)** | Clone + run (below) |
| **Phone → your PC** | Open your public tunnel (e.g. `https://pocket.medinatechlabs.net`) with invite credentials |

```text
Landing  →  /get (install guide)
         →  /download  (Windows .exe)
         →  /desk      (multi-agent console)
         →  /developers (API)
```

## Quick start (operator host)

**Requirements:** Python 3.11+, Windows recommended. Optional: [Grok CLI](https://x.ai), [Codex CLI](https://github.com/openai/codex).

```powershell
git clone https://github.com/FreddyCreates/pocket.git
cd pocket
$env:PYTHONPATH = "$PWD\src"
python -m pocket serve --host 127.0.0.1 --port 8787
```

Open **http://127.0.0.1:8787/desk**

Or:

```powershell
.\Start-POCKET.ps1
```

Password / access file (local, not in git): `%USERPROFILE%\.pocket\ACCESS.txt`

## What you get

- **Agents:** Codex · Grok · Claude · Plan · Offload · ARCHON · Browser · Desktop · NEXUS · MESIE · …
- **AI workspace:** auto context + summary so agents don’t re-scan the tree every turn
- **Offload / embodiment:** background real-world tasks + proof packs
- **Agent bus:** hashed mesh envelopes for multi-agent handoffs
- **Desktop app:** Electron portable under `releases/desktop/` (build scripts in `desktop-electron/`)
- **API:** `sk_pocket_` keys · headless agents · metering (`docs/AI_API.md`)

## Docs

| Doc | Topic |
|-----|--------|
| [PRODUCT.md](PRODUCT.md) | Product surfaces |
| [docs/AI_WORKSPACE.md](docs/AI_WORKSPACE.md) | Token-saving AI workspace |
| [docs/EMBODIMENT_OFFLOAD.md](docs/EMBODIMENT_OFFLOAD.md) | Real-world offload |
| [docs/PRODUCTION.md](docs/PRODUCTION.md) | Production A→Z (if present) |
| [USE_NOW.md](USE_NOW.md) | Operator runbook |

## Safety

- App allowlist · shell policy · URL policy · audit log  
- **No secrets in this repo** — keys and access stay under `~/.pocket/`  
- Financial paths (e.g. PARALLAX) stay **paper/testnet-first** unless you gate otherwise  

## Version

Ship channel: **desktop 2.0.x-alpha** · host multi-agent desk active.

## License

See [LICENSE](LICENSE) if present; otherwise all rights reserved pending license file.
