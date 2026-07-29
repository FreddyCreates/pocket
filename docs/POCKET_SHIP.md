# POCKET — ship brief

**Name:** POCKET (POCKET OS)  
**Ships:** Phone Grok coding platform  

## Promise

Code and instruct suite agents from your phone. Queue lands on the PC for Grok / terminal / away-watch.

## Boot

```powershell
$env:PYTHONPATH = "C:\Users\Medin\OneDrive\pocket-os\src;C:\Users\Medin\OneDrive\hz-offline\src"
python -m pocket serve --port 8787
# other terminal:
python -m pocket watch
```

Phone: `http://<LAN-IP>:8787/`

## Ports

| Port | Product |
|------|---------|
| 8765 | HZ Hub multi-user chat |
| 8787 | **POCKET** coding platform |
| 5174 | MonadBuilder |
| 8043 | THESIS API |

## Suite lanes on phone

SignalLens · NEXUS · MESIE · HZ · Auro-4B · Mini Novas · MonadBuilder+
