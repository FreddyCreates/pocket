# POCKET — real Cloudflare Named Tunnel (far away / phone)

Quick tunnels (`*.trycloudflare.com`) flap and 530.  
With a **paid Cloudflare account** + a domain on CF DNS, use a **named tunnel**.

## One-time setup (interactive)

1. Own a domain on Cloudflare (DNS active).
2. Pick a hostname, e.g. `pocket.yourdomain.com`.
3. In **interactive** PowerShell (browser login):

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Medin\OneDrive\pocket-os\scripts\Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.yourdomain.com
```

This will:
- Open Cloudflare login (stores `~\.cloudflared\cert.pem`)
- Create tunnel `pocket-os`
- Write `~\.cloudflared\config.yml` → `http://127.0.0.1:8787`
- Create DNS CNAME for your hostname
- Save URL to `~\.pocket\PUBLIC_URL.txt` and `cloudflare-named.env`

### Always-on tunnel (Admin once)

```powershell
# Run PowerShell as Administrator
powershell -ExecutionPolicy Bypass -File C:\Users\Medin\OneDrive\pocket-os\scripts\Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.yourdomain.com -InstallService -SkipLogin
```

## Every day / keep alive

**POCKET** (local server):
```powershell
powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\Start-POCKET-NoAdmin.ps1
```

**Named tunnel** (if not installed as service):
```powershell
powershell -File C:\Users\Medin\OneDrive\pocket-os\scripts\Start-Cloudflare-Named.ps1
```

## Phone from anywhere

`https://pocket.yourdomain.com/`  
(whatever hostname you chose)

## Security notes

- Public URL exposes your multi-agent desk. Prefer Access / password later.
- Only route what you need (POCKET :8787). Don’t expose whole LAN.
- PC must be **awake** and POCKET + tunnel **running**.

## Verify

```powershell
cloudflared tunnel list
cloudflared tunnel info pocket-os
curl https://pocket.yourdomain.com/health
```
