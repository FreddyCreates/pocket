# POCKET — ship for users (product mode)

## The three ways to use it

| Surface | Who | How they open it |
|---------|-----|------------------|
| **Edge app (local)** | You / same Wi‑Fi | Desktop shortcut **POCKET** → auto-starts host → Edge `--app=` desk |
| **Electron .exe** | Download users | **POCKET Electron** shortcut or GitHub Release / `/download` |
| **Cloudflare URL** | Phone / remote users | https://pocket.medinatechlabs.net (tunnel must stay Automatic) |

**Rule for agents/operators:** never kill a healthy host or cloudflared just to “restart.” Only start if **down**.

## Install once (this PC)

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Medin\OneDrive\pocket-os\scripts\Install-POCKET-Ship.ps1
```

That installs:

1. **Always-on** watchdog in Windows Startup  
2. Host ensure-if-down  
3. Desktop + Start Menu shortcuts  

Then you open **POCKET** like any other app — double-click.

## Multi-user (already in product)

| File | Role |
|------|------|
| `~/.pocket/INVITE.txt` | Share invite code |
| Login panel | Register with invite + password |
| `~/.pocket/users.json` | Accounts + roles |

Flow for a new user:

1. You share invite code + either Cloudflare URL or they install Electron against their own host later.  
2. They open desk → **Register** with invite.  
3. They use agents under their seat (RBAC + quotas).

## Cloudflare vs Edge app

| | Cloudflare | Edge app (local) |
|--|------------|------------------|
| Needs | cloudflared service **Automatic** + host on `:8787` | Host on this PC only |
| Use | Phone, far away, multi-user public | You at the desk, fastest |
| Breaks if | Host killed, tunnel stopped | Host not running (shortcut fixes this) |

Both talk to the **same product**. Do not thrash the host.

## Funnel (later website on CF)

```text
Marketing site (CF Pages)
  → Pay / account
  → Download Electron  (/download or GitHub Releases)
  → Or “Open my seat” → pocket.medinatechlabs.net/desk
  → Or “Install Edge app” instructions (/get)
```

Ship install first; marketing polish second.

## Downloads

- Local: http://127.0.0.1:8787/download  
- Public: https://pocket.medinatechlabs.net/download  
- GitHub: https://github.com/FreddyCreates/pocket/releases  

## Health

```powershell
# Should NOT kill anything — only starts if needed
powershell -File ...\scripts\Ensure-POCKET-Up.ps1
```
