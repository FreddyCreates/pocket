# POCKET Production — A→Z for real users

**Version:** 1.2.0  
**Audience:** Operator shipping invite-only seats + sellable AI API  
**Trust model:** Single host PC · invite multi-user · role gates · **not** public multi-tenant SaaS

## One-line status

Production-ready for **trusted invited users** and **API customers with keys**, when the host stays online.  
Not ready for untrusted anonymous multi-tenant cloud without per-user OS sandbox.

## A→Z checklist

| | Item | Done when |
|--|------|-----------|
| **A** | Auth | `~/.pocket/access.env` + login; token preferred over password in browser |
| **B** | Multi-user | Invite register; roles admin/member |
| **C** | Cloudflare | Named tunnel → public URL; optional Access |
| **D** | Desk agents | Codex/Grok/Plan/Web/Desktop/NEXUS |
| **E** | RBAC | Members blocked from shell/term/wsl; admin-only mint/deploy |
| **F** | Files | State in `~/.pocket` |
| **G** | Invite | `INVITE.txt`; rotate with admin API |
| **H** | Health | `/health` + `/v1/ready` |
| **I** | Isolation | Sessions owned; list/get/delete scoped |
| **J** | Jobs | Worker pool; orphan reclaim on boot |
| **K** | API keys | `sk_pocket_…`; hashed; quota enforced |
| **L** | Legal | `docs/LEGAL.md` + UI accept on register |
| **M** | Metering | POCK burns; API usage by key |
| **N** | NEXUS | Optional intelligence workers |
| **O** | Onboarding | First-run UI + ready matrix |
| **P** | Production matrix | `GET /v1/ready` |
| **Q** | Quotas | Monthly call quota hard-stop |
| **R** | Rate limits | Login/register/API |
| **S** | Safety | App/URL/shell allowlists + audit |
| **T** | Tunnel | cloudflared service |
| **U** | Users | Admin exists; change password; logout |
| **V** | Version | 1.2.0 product |
| **W** | Watchdog | `python -m pocket runtime` + Startup |
| **X** | Headers | CSP, nosniff, frame deny |
| **Y** | Backup | `scripts/Backup-POCKET.ps1` |
| **Z** | Zero-trust honesty | Documented single-host model |

## Operator go-live (30 min)

1. `Start-POCKET.ps1` — leave running, PC awake  
2. `python -m pocket doctor` and `GET /v1/ready` all P0 green  
3. Confirm public: `https://YOUR_HOST/health`  
4. Share invite from `%USERPROFILE%\.pocket\INVITE.txt` only with trusted people  
5. Create API keys for customers: desk **Headless AI API → New API key**  
6. Run backup: `scripts\Backup-POCKET.ps1`  
7. Prefer Cloudflare Access in front of the hostname for production internet  

## Member capabilities

| Allowed | Blocked (admin only) |
|---------|----------------------|
| Plan, Web, Codex, Grok, NEXUS, Desktop allowlist | Shell, WSL, live Terminal |
| Own sessions | Other users’ sessions |
| Own API keys (quota) | Mint POCK, deploy processes, ops agent |

## Customer API go-live

```http
GET  /v1/ai
POST /v1/ai/keys          # admin
POST /v1/ai/chat
POST /v1/ai/agents/{id}/run
GET  /v1/ai/usage
```

Docs: `docs/AI_API.md` · Legal: `docs/LEGAL.md`

## Verify

```powershell
Invoke-RestMethod http://127.0.0.1:8787/v1/ready
Invoke-RestMethod http://127.0.0.1:8787/health
```

## Still later (true SaaS)

- Per-user OS sandbox / containers  
- Stripe + invoices  
- Email verify / password reset mail  
- Mandatory Cloudflare Access  
- Webhooks for async jobs  
