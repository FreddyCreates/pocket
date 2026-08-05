# POCKET security (public tunnel)

## Founder files vs market (non‑negotiable)

| Edition | Sees founder disk? | Local + virtual |
|---------|--------------------|-----------------|
| **Founder** (admin/operator) | Yes — this is their machine | Full host + virtual |
| **Market seat** | **Never** | Only `~/.pocket/tenants/<user>/` |

Market jobs cannot cwd into OneDrive/Parallax/pocket-os. Host desktop / shell / **WSL** / capture are founder-only on a shared operator host.

See [PRODUCT_EDITIONS.md](PRODUCT_EDITIONS.md) · [wsl/WSL_NATIVE.md](wsl/WSL_NATIVE.md).

## What is locked

| Surface | Access |
|---------|--------|
| `/health` | Public (tunnel / uptime only) |
| `/`, `/desk`, `/phone` shells | Public HTML; APIs need auth |
| `/download` binaries | **Researcher License accept** required |
| All sensitive `/v1/*` APIs | **Password / seat / API key** |
| Deploy / shell / desktop / WSL / mint | **Founder only** |
| Market file APIs | **Own tenant only** |

## Credentials

- File: `%USERPROFILE%\.pocket\ACCESS.txt`
- Env: `%USERPROFILE%\.pocket\access.env`
- User default: `pocket`
- Header options: `Authorization: Basic …`, `Bearer` session token, or `X-Pocket-Access: <password>`

## Protections

1. **Auth on sensitive routes** (401 without password/seat/API key)
2. **Rate limit** failed logins (12 / 5 min / IP → 429)
3. **Security headers** — CSP, X-Frame-Options DENY, nosniff, no-store, COOP/CORP, tight Permissions-Policy
4. **Body size cap** 2MB
5. **Shell + WSL blocklists** for destructive patterns (pipe-to-shell, root wipe, fork bombs)
6. **CORS not open** to arbitrary sites
7. **Password stored only on disk** — not returned by API
8. **Researcher License gate** on binary downloads (`POST /v1/license/accept` → cookie/token)
9. **Edition isolation** — market jobs forced into tenant trees via `ensure_job_isolation`

## Still your responsibility

- Keep PC password-locked
- Don’t share ACCESS.txt
- Prefer Cloudflare Access later for SSO
- Sleep/hibernate = offline
- Agents can write files when you run Codex/Grok with approve flags
- Public research downloads ≠ commercial SaaS rights

## Verify

```powershell
# should 401
curl -i https://pocket.medinatechlabs.net/v1/status
# should 200
curl -i https://pocket.medinatechlabs.net/health
# should 403 without license
curl -i https://pocket.medinatechlabs.net/download/desktop
```
