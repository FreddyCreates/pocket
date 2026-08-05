<p align="center">
  <img src="docs/brand/pocket-mark.svg" width="120" alt="POCKET"/>
</p>

<h1 align="center">POCKET</h1>

<p align="center">
  <b>Company multi-agent host platform</b><br/>
  ItsNotAI Labs · Medina Tech Labs<br/>
  Edge desk · team seats · Cloudflare · sellable API · your infrastructure
</p>

<p align="center">
  <a href="https://github.com/ItsNotAILABS/pocket"><img alt="Org" src="https://img.shields.io/badge/org-ItsNotAILABS-0b6e4f?style=flat-square&logo=github"/></a>
  <a href="https://github.com/ItsNotAILABS/pocket/releases"><img alt="Releases" src="https://img.shields.io/badge/releases-company-1d4ed8?style=flat-square"/></a>
  <img alt="Edition" src="https://img.shields.io/badge/edition-company-10b981?style=flat-square"/>
</p>

---

## Company product (not a personal toy)

| | |
|--|--|
| **Company** | Medina Tech Labs |
| **Lab** | ItsNotAI Labs |
| **Org** | [ItsNotAILABS](https://github.com/ItsNotAILABS) |
| **Edition** | **company** — team seats, RBAC, founder disk ≠ market seats |
| **Host** | Your PC / server (sovereign) |
| **Public desk** | `https://pocket.medinatechlabs.net` (when tunnel is up) |

### Isolation rule

- **Owner / operator** — full host (ACCESS.txt)
- **Team members** — invite seat (`pk_seat_…`), own username/password, sandbox only  
- Market never browses the founder’s personal disk

---

## Get it running (operator)

```powershell
# One-time: shortcuts + always-on
powershell -ExecutionPolicy Bypass -File scripts\Install-POCKET-Ship.ps1

# Or start host now
$env:PYTHONPATH = "$PWD\src"
python -m pocket serve --host 0.0.0.0 --port 8787
```

Then open **Desktop → POCKET** (Edge app) or http://127.0.0.1:8787/desk

**Owner login:** username `pocket` + password in `%USERPROFILE%\.pocket\ACCESS.txt`

---

## Surfaces

| Surface | URL |
|---------|-----|
| Desk | `/desk` |
| Phone | `/phone` |
| Overview | `/tour` |
| Get / install | `/get` |
| API | `/developers` |
| Health | `/health` |
| Class / ready | `/v1/class` · `/v1/ready` |

---

## Multi-user (company seats)

```http
POST /v1/admin/invites
{ "label": "alice", "max_uses": 1 }
→ invite_key pk_seat_…
```

Member: desk → **Create my seat** → their own credentials.

See [docs/MULTI_USER.md](docs/MULTI_USER.md).

---

## Real verification

```powershell
powershell -File scripts\real-product.ps1
```

---

## Repo

https://github.com/ItsNotAILABS/pocket
