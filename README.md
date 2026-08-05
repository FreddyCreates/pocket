<p align="center">
  <img src="docs/brand/pocket-mark.svg" width="120" alt="POCKET"/>
</p>

<h1 align="center">POCKET</h1>

<p align="center">
  <b>Multi-agent host co-pilot</b> — your machine, your seats, real agents.<br/>
  Edge app · Electron · Cloudflare desk · invite-gated multi-user
</p>

<p align="center">
  <a href="https://github.com/FreddyCreates/pocket/releases">Releases</a> ·
  <a href="https://github.com/FreddyCreates/pocket-app">User app hub</a> ·
  <a href="docs/SHIP_FOR_USERS.md">Ship guide</a> ·
  <a href="docs/MULTI_USER.md">Multi-user</a>
</p>

---

## Get it

| Door | Who | Link |
|------|-----|------|
| **Edge app (local)** | You on this PC | Desktop shortcut **POCKET** (after ship install) |
| **Electron** | Download users | [Releases](https://github.com/FreddyCreates/pocket/releases) · host `/download` |
| **Cloud desk** | Phone / remote | your tunnel e.g. `https://pocket.medinatechlabs.net/desk` |
| **Source (operators)** | Host builders | this repo |

```powershell
# Operator PC — one-time ship install (shortcuts + always-on)
powershell -ExecutionPolicy Bypass -File scripts\Install-POCKET-Ship.ps1
# Then double-click Desktop "POCKET"
```

## Multi-user (not “log into owner”)

- **Owner** = you (`ACCESS.txt` / admin). Stays owner.
- **Members** get a **`pk_seat_…` cryptographic key** (SHA-256 stored server-side).
- They open **Create my seat**, pick **their** username + password.
- They never use your password. Invite ≠ login.

```http
POST /v1/admin/invites
{ "label": "alice", "max_uses": 1 }
→ { "invite_key": "pk_seat_…", "message": "Give to user; they create OWN account" }
```

See [docs/MULTI_USER.md](docs/MULTI_USER.md).

## Product surfaces

- **Desk** — Codex · Grok · Claude · Cowork · Git · Offload · Auro  
- **Forge** — `/forge` sovereign git vault  
- **Auro** — `/auro/` browser meaning piece  
- **API** — `/developers` sellable agents  

## Always-on

Host should stay up. Shortcuts call **ensure-if-down** only — they do not thrash Cloudflare.

```powershell
scripts\Ensure-POCKET-Up.ps1   # start only if down
scripts\Start-POCKET-AlwaysOn.ps1
```

## License

**POCKET Researcher License** (non-commercial research & evaluation) — see [LICENSE-RESEARCHER.md](LICENSE-RESEARCHER.md).  
Downloads require license accept (`/download`). Commercial use needs a written license.

**Lab:** ItsNotAI Labs / Medina Tech Labs

## Docs & downloads

| Path | What |
|------|------|
| `/docs/hub` | Documentation hub |
| `/download` | Packages (researcher gate) |
| `/license` | License summary |
| `/phone` | Mobile web app |
| `docs/wsl/WSL_NATIVE.md` | Native WSL agent story |
| `REPOS.md` | Repository map |
