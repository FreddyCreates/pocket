# POCKET — ship for users (product mode)

## Two client modes (test both)

| Shortcut | Who | First open |
|----------|-----|------------|
| **POCKET Owner** | You / operator | Local host only — **no** source wizard |
| **POCKET User Test** | Members / download users | **Source picker** → cloud / local / custom → desk → Create my seat |
| **POCKET** (Edge) | You on this PC | Edge app → local desk (ensure-if-down) |

Owner and User use **separate Electron profiles** (`%APPDATA%\POCKET-Owner` vs `POCKET-User`) so testing one never overwrites the other.

## What happens when a **user** opens POCKET

```text
1. Launch (POCKET_CLIENT_ROLE=user or packaged install)
2. If no saved desk → onboarding.html
   a. Pick source:
      • Team/cloud desk  → enter https URL (probe /health)
      • This computer    → ensure local host on :8787
      • Custom URL       → any https origin
   b. Save only { source, baseUrl } — never password or pk_seat_
3. Open {baseUrl}/desk
4. Create my seat (pk_seat_…) or Sign in as yourself
5. Next launch: skip wizard, open saved desk
   (Menu → Change desk source… to re-pick)
```

Owner path never runs steps 2a–2b.

## The three surfaces

| Surface | Who | How they open it |
|---------|-----|------------------|
| **Edge app (local)** | You / same Wi‑Fi | Desktop **POCKET** |
| **Electron .exe** | Download users | User hub / Releases — first-run picker |
| **Cloudflare URL** | Phone / remote | https://pocket.medinatechlabs.net/desk |

**Rule for agents/operators:** never kill a healthy host or cloudflared. Only start if **down**.

## Install once (this PC)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Install-POCKET-Ship.ps1
```

That installs always-on + dual Desktop shortcuts for Owner and User Test.

## Multi-user (not “share owner login”)

1. Owner mints **`pk_seat_…`** (SHA-256 on server, max uses / expiry).
2. Member opens **user** client → picks desk source → **Create my seat**.
3. Member chooses **their** username + password.
4. Owner session stays owner. Member is a seat, not admin (unless granted).

See [MULTI_USER.md](MULTI_USER.md).

## Public repos (no secrets)

| Repo | Role |
|------|------|
| [FreddyCreates/pocket](https://github.com/FreddyCreates/pocket) | Product source |
| [FreddyCreates/pocket-app](https://github.com/FreddyCreates/pocket-app) | User-facing hub |

Never commit: `ACCESS.txt`, invite keys, `users.json`, API keys, tunnel tokens, `.env`.

## Downloads

- Local: http://127.0.0.1:8787/download  
- Public: https://pocket.medinatechlabs.net/download  
- GitHub: https://github.com/FreddyCreates/pocket/releases  
