# POCKET repository map (ItsNotAI Labs)

Organize public surface around **product**, **app hub**, and **research** — not personal clutter.

## Public product surface

| Repo | Role | License |
|------|------|---------|
| **pocket** (`FreddyCreates/pocket` → prefer `ItsNotAILABS/pocket`) | Core host runtime, desk, phone, API, WSL agent, docs | **Researcher License** |
| **pocket-app** | User hub: downloads, docs, seats, Edge/Electron doors | **Researcher License** |

## Related lab systems (separate products)

| Repo / org | Role |
|------------|------|
| `ItsNotAILABS/*` | Company org — primary home for public lab work |
| MESIE, Auro14B, NEXUS / MERIDIAN | Spectral / LMR / intelligence stacks — link from pocket docs, keep separate |
| AIFX, Parallax, etc. | Domain products — do **not** dump into pocket |

## What stays off public product repos

- Operator `ACCESS.txt` / secrets / `.env`  
- Founder personal OneDrive trees  
- Tenant data under `~/.pocket/tenants/`  
- Mesh keys, API key material, session tokens  

## Local layout (this machine)

```text
OneDrive/pocket-os/     ← operator source of truth (host)
  src/pocket/           runtime
  docs/                 product docs
  desktop-electron/     shell package
  releases/desktop/     built .exe artifacts
  LICENSE-RESEARCHER.md
  REPOS.md              ← this file

OneDrive/pocket-app/    ← market/docs hub mirror
  README.md
  docs/
  LICENSE

~/.pocket/              runtime state (never commit)
```

## Naming convention

- Product repos: `pocket`, `pocket-app`  
- Docs paths: `docs/security`, `docs/wsl`, `docs/license`  
- Public downloads: only via `/download` after Researcher License accept  

## Transfer target (company posture)

When ready: move `pocket` + `pocket-app` under **`ItsNotAILABS`** so GitHub shows org ownership, not a personal hobby profile.
