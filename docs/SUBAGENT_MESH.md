# POCKET Subagent Mesh (E: Virtual Disk)

**Protocol:** `MEDINA-SUBAGENT-MESH/1.0` · **Archival:** `INL-2026-POCKET.MESH.v1`  
**Always-use hook:** `pocket.agent_hook.ensure_mesh_hook()` (armed on `serve()`)  
**Research:** `docs/research/POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md` (+ `.pdf`)  
**API:** `GET /v1/protocols/mesh` · `POST /v1/hooks/mesh`

## Overview

Antigravity-style: subagents **message and leave artifacts without sharing a chat**.

| Path | Purpose |
|------|---------|
| `E:\POCKET_MESH` | Virtual mesh root (prefer E: 5TB) |
| `agents/<ID>/inbox\|outbox\|artifacts\|keys` | Per-agent mailbox |
| `channels/freq-N.jsonl` | Frequency buses |
| `vdisk/workspaces/<ID>/` | Virtual disk file offload |
| `workers/*.py` | Headless Python workers on E: |
| `protocols/{microsoft,bluetooth,hz}` | Host + Hz protocol docs |

Identity: `SHA-256(salt || agent_id)`.  
Envelopes: **HMAC-SHA256** + optional **body_cipher** (`hmac-sha256-xor-v1`).

## Agents (≥10 + 4 headless)

**Latin:** ARCHON, HYDRA, SCRUTATOR, SCRIPTOR, PORTARIUS, OCULUS, SPECULUM, REPOSITOR, CONSILIARIUS, TABELLARIUS, NAVIGATOR, GUPPY  

**Design:** DESIGN, AESTHETE, LAYOUT, MOTION  

**Headless (powerful):** FORGE_HEADLESS, SENTINEL_HEADLESS, RESEARCH_HEADLESS, SHIP_HEADLESS  

## @dispatch

```
POST /v1/subagents/dispatch  { "message": "@DESIGN polish composer", "name": "DESIGN" }
GET  /v1/subagents
GET  /v1/mesh
POST /v1/mesh/bootstrap
POST /v1/headless/start
```

Composer: type `@` for autocomplete (Latin + design + headless).

## Hz lanes

| Lane | Channel | Use |
|------|---------|-----|
| user | freq-0 | @dispatch |
| heartbeat | freq-1 | headless pulse |
| design | freq-2 | design bus |
| security | freq-3 | sentinel |
| ship | freq-4 | release |
| intel | freq-5 | research / BLE stubs |

## Python modules

- `pocket.mesh_disk` — virtual disk + crypto mail  
- `pocket.subagent_dispatch` — @mentions + headless  
- `pocket.design_agents` — design specialists  
- `pocket.ms_protocol` — Microsoft/UIA bridges  
- `pocket.hz_mesh` — frequency channels  
- `E:\POCKET_MESH\workers\worker_*.py` — offload writers  

## Virtual disk (not OS VHD)

We use a **logical virtual workspace** on E: rather than mounting a `.vhd`. Same goal: isolate agent I/O onto high-capacity storage, keep C: clean, let workers write files independently of chat.
