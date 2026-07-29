# POCKET security (public tunnel)

## What is locked

| Surface | Access |
|---------|--------|
| `/health` | Public (tunnel / uptime only) |
| `/` UI shell | Public (login form only) |
| All `/v1/*` APIs | **Password required** |
| Deploy / shell / agents / mint | **Password required** |

## Credentials

- File: `%USERPROFILE%\.pocket\ACCESS.txt`
- Env: `%USERPROFILE%\.pocket\access.env`
- User default: `pocket`
- Header options: `Authorization: Basic …` or `X-Pocket-Access: <password>`

## Protections

1. **Auth on all sensitive routes** (401 without password)
2. **Rate limit** failed logins (12 / 5 min / IP → 429)
3. **Security headers** (CSP, X-Frame-Options DENY, nosniff, no-store)
4. **Body size cap** 2MB
5. **Shell blocklist** for destructive patterns
6. **CORS not open** to arbitrary sites
7. **Password stored only on disk** — not returned by API

## Still your responsibility

- Keep PC password-locked
- Don’t share ACCESS.txt
- Prefer Cloudflare Access later for SSO
- Sleep/hibernate = offline
- Agents can write files when you run Codex/Grok with approve flags

## Verify

```powershell
# should 401
curl -i https://pocket.medinatechlabs.net/v1/status
# should 200
curl -i https://pocket.medinatechlabs.net/health
```
