# POCKET Subagent Mesh — Beta Operator Notes

**Companion to:** `POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md`  
**Archival code:** `INL-2026-POCKET.MESH.v1`  
**Date:** 2026-07-28 · ItsNotAI Labs / Medina Tech Labs  

Short checklist only. Full architecture, doctrine, and measured-vs-planned tables live in the research report.

---

## 0. Doctrine (30 seconds)

**MEDINA Subagent Mesh Protocol (MSMP-1.0)** — multi-agent work goes through the mesh (mail + artifacts + channels), not only the chat transcript.

- Prefer `@AGENT` dispatch  
- Prefer `E:\POCKET_MESH` when present  
- DESIGN is first-class (never SCRIPTOR)  
- Do not invent benchmarks; mark planned vs measured  

---

## 1. Pre-flight

| # | Check | How |
|---|--------|-----|
| 1 | POCKET server up | Desk / `http://127.0.0.1:8787/` (or your bound port) |
| 2 | Mesh root | `GET /v1/mesh` → `mesh_root` should prefer `E:\POCKET_MESH` |
| 3 | Agent pack | `agent_count` ≥ 20 after bootstrap |
| 4 | Auth | Use existing POCKET session / API key as required by your install |
| 5 | Volume free space | E: has room for artifacts + recordings |

Optional env override: `POCKET_MESH_ROOT` (absolute path).

---

## 2. Bootstrap sequence

```http
GET  /v1/mesh
POST /v1/mesh/bootstrap
# or
POST /v1/headless/start
{"interval": 120}
```

Expect:

- `bootstrap.agents` includes Latin + Design + Headless  
- `headless` pack started (or `already: true`)  
- `protocols/microsoft|bluetooth|hz` folders under mesh root  

Stop headless when done with long demos:

```http
POST /v1/headless/stop
```

---

## 3. Real dispatch (order matters)

| Step | Action | Pass criteria |
|------|--------|----------------|
| A | `POST /v1/subagents/dispatch` `{"message":"@DESIGN polish composer"}` | `ok`, artifact paths under DESIGN |
| B | Open `E:\POCKET_MESH\agents\DESIGN\artifacts\` | critique `.md` + snippet `.css` |
| C | `GET /v1/mesh/channel?name=freq-2` | recent design traffic (if design channel used) |
| D | `POST …` `{"message":"@FORGE_HEADLESS real"}` | forge artifact and/or E: worker stdout |
| E | `POST …` `{"message":"@SHIP_HEADLESS beta gate"}` | `SHIP_CHECKLIST.md` |
| F | `GET /v1/mesh/inbox/ARCHON` | status/heartbeat/dispatch notices; `valid_hmac` true when signed |
| G | Composer `@` autocomplete | Latin + design + headless names appear |

Raw mail (no host skill):

```http
POST /v1/mesh/send
{"from":"USER","to":"ARCHON","body":"ping","channel":"freq-0"}
```

---

## 4. Frequency lanes (operator cheat sheet)

| Lane | Channel | Use |
|------|---------|-----|
| user | `freq-0` | Default @dispatch |
| heartbeat | `freq-1` | Headless pulse |
| design | `freq-2` | DESIGN pack bus |
| security | `freq-3` | Sentinel |
| ship | `freq-4` | Release / beta |
| intel | `freq-5` | Research / BLE stubs |

If a `freq-N.jsonl` file is missing, first publish creates it.

---

## 5. Agent packs (quick roster)

**Latin (12):** ARCHON, HYDRA, SCRUTATOR, SCRIPTOR, PORTARIUS, OCULUS, SPECULUM, REPOSITOR, CONSILIARIUS, TABELLARIUS, NAVIGATOR, GUPPY  

**Design (4):** DESIGN, AESTHETE, LAYOUT, MOTION  

**Headless (4):** FORGE_HEADLESS, SENTINEL_HEADLESS, RESEARCH_HEADLESS, SHIP_HEADLESS  

Aliases (dispatch): `@UI`/`@UX`→DESIGN · `@GRID`→LAYOUT · `@FORGE`→FORGE_HEADLESS · `@SHIP`→SHIP_HEADLESS · `@VISION`→OCULUS  

---

## 6. Paths to know

| Path | Why |
|------|-----|
| `E:\POCKET_MESH` | Mesh root |
| `…\agents\<ID>\inbox` | Incoming envelopes |
| `…\agents\<ID>\artifacts` | Work products |
| `…\channels\freq-*.jsonl` | Shared buses |
| `…\workers\worker_*.py` | Headless offload scripts |
| `…\vdisk\workspaces\<ID>\` | Virtual disk files |
| `…\protocols\` | Protocol READMEs |

---

## 7. Modules (debug)

| Symptom | Look at |
|---------|---------|
| No mesh / wrong drive | `pocket.mesh_disk` root pick |
| @mention no-op | `pocket.subagent_dispatch` + `server` routes |
| Design weak / wrong agent | `pocket.design_agents` (DESIGN not SCRIPTOR) |
| Roster incomplete | `pocket.subagents_panel` |
| Hz / BLE map | `pocket.hz_mesh`, `pocket.protocols.bluetooth_hz` |
| Host click / open app | `pocket.protocols.microsoft_protocol` |
| UI soft-fail dispatch | `pocket.app_ui` fetch to `/v1/subagents/dispatch` |
| Orchestrator skill path | `pocket.orchestrator_exec` (`subagents_dispatch`) |

`agent_hook`: not a separate file yet — hooks are the call sites above (MSMP always-use).

---

## 8. CloudColony / Triple Protocol (beta framing)

| Layer | Meaning for operators |
|-------|------------------------|
| **POCKET** | Product you run locally — MSMP mesh is here |
| **MESIE** | Compute / spectral lane workspace (when installed) |
| **CloudColony** | Framework wrap — Triple Protocol, colony MCP, optional bridge |

Triple Protocol (ecosystem): **P1** MEDINA-LOOM · **P2** MEDINA-MCP-COLONY-DEPLOY · **P3** MEDINA-COLONY-BRIDGE  

Local beta **does not require** ICP mainnet. SHIP checklist may still mention the CloudColony framework repo — verify path on your machine.

---

## 9. Demo safety

- Prefer allow-listed apps via PORTARIUS / microsoft protocol  
- SENTINEL uses guarded shell probes — do not bypass with raw PS  
- TABELLARIUS drafts; do not assume send  
- Screen record (SPECULUM) needs ffmpeg / host tools as installed  
- Encrypted channel logs still live on disk — treat mesh root as sensitive  

---

## 10. Ship gate (minimal)

Copy from SHIP_HEADLESS spirit:

- [ ] Desktop / tray path works  
- [ ] API keys / developers surface  
- [ ] Product nav Overview · Desktop · API · Studio  
- [ ] Fusion sense + RFE path known  
- [ ] Subagents `@` dispatch works  
- [ ] Mesh on E: (or documented fallback)  
- [ ] Design agents produce artifacts  
- [ ] Protocols microsoft + bluetooth + hz folders exist  
- [ ] CloudColony framework repo location known  
- [ ] No fake benchmark slides  

---

## 11. Measured vs planned (operator honesty)

| Say this | Only if |
|----------|---------|
| “Mesh is live on E:” | `GET /v1/mesh` shows it and tree exists |
| “Encrypted agent mail” | envelopes show `body_cipher` + valid HMAC |
| “Headless pack running” | heartbeats / threads started this session |
| “BLE mesh” | **Do not** — radio is planned; file-bus only |
| “Colony federation” | **Do not** claim unless Triple Bridge proven on this host |
| “p50 latency X ms” | **Do not** invent — run a harness first |

---

## 12. One-liner for funders

> POCKET runs a host-local subagent mesh (MSMP): named agents leave signed, optionally encrypted artifacts on a high-capacity virtual mesh disk—chat is intake; CloudColony is the framework wrap.

---

*End of beta notes. Full paper: `POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md`*
