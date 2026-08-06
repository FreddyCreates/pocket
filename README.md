<p align="center">
  <img src="docs/brand/pocket-mark.svg" width="120" alt="POCKET"/>
</p>

<h1 align="center">POCKET</h1>

<p align="center">
  <b>Company multi-agent workstation</b><br/>
  ItsNotAI Labs · Medina Tech Labs<br/>
  Desktop app · Edge app · Cloudflare account · team seats · sellable API
</p>

---

## Product channels

POCKET is no longer one development server exposed through a tunnel.

| Channel | Purpose |
|---|---|
| **POCKET Desktop** | Installable Electron app with a bundled local `pocket-host.exe`, Desktop/Start-menu shortcuts, tray mode, and optional start-at-login. |
| **POCKET Edge App** | The same local engine in a Microsoft Edge app window for users who prefer the existing Edge surface. |
| **POCKET Cloud Account** | Independent Cloudflare Worker + D1 + R2 account, organization, invitation, paired-device, task relay, and entitlement-gated download plane. |

Read [POCKET Product Channels v3](docs/POCKET_PRODUCT_CHANNELS_V3.md).

### Availability rule

- Opening Electron or the Edge launcher starts or reuses the packaged local engine.
- A healthy engine is never restarted.
- An unknown listener is never killed automatically.
- The Cloudflare account stays online without depending on the operator's local port or Cloudflare Tunnel.
- A paired desktop only needs to be online when a cloud task requires local execution.

## Isolation

- **Owner/operator** — full local founder host.
- **Cloud organization members** — their own account and organization role.
- **Local market members** — their own credentials and tenant sandbox.
- A paired cloud device receives a restricted `sk_pocket_*` key, not the founder owner session.

## Build POCKET Desktop

```powershell
.\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch auto
```

Build both Windows architectures:

```powershell
.\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch both
```

Developer modes:

```powershell
cd desktop-electron
npm install
npm run start:local
npm run start:cloud
npm run start:edge
```

## Deploy POCKET Cloud

Provision D1 and R2 once, configure `BOOTSTRAP_TOKEN` and `RELEASE_ADMIN_TOKEN`, then:

```powershell
$env:POCKET_D1_DATABASE_ID = "your-d1-id"
.\scripts\Deploy-POCKET-Cloud.ps1
```

Validate the generated Worker URL before changing any existing tunnel or production DNS. See [POCKET Cloud Account](docs/POCKET_CLOUD_ACCOUNT.md).

## Existing local surfaces

| Surface | URL |
|---|---|
| Desk | `/desk` |
| Phone | `/phone` |
| Overview | `/tour` |
| Get/install | `/get` |
| API | `/developers` |
| Health | `/health` |
| Class/ready | `/v1/class` · `/v1/ready` |

## Multi-user

Cloud organizations use D1-backed owner/admin/member/viewer memberships and expiring invite codes. The existing local host retains its separate seat system and founder/market isolation.

See [docs/MULTI_USER.md](docs/MULTI_USER.md) and [docs/POCKET_PRODUCT_CHANNELS_V3.md](docs/POCKET_PRODUCT_CHANNELS_V3.md).

## Evidence boundary

A merged source branch is not proof of a live Cloudflare deployment or a downloadable Windows binary. Those claims require the protected deployment workflow, Windows release artifacts, checksums, and clean-install evidence in [docs/POCKET_RELEASE_RUNBOOK.md](docs/POCKET_RELEASE_RUNBOOK.md).

## Repository

https://github.com/ItsNotAILABS/pocket
