# POCKET Subagent Mesh Protocol & CloudColony Wrap — Research Report

**Date:** 2026-07-28  
**Lab:** ItsNotAI Labs / Medina Tech Labs  
**Classification:** Strategic Engineering / Architecture / Beta Operator Brief  
**Archival code:** `INL-2026-POCKET.MESH.v1`  
**Related:** `INL-2026-POCKET.RFE.v1` · `INL-2026-POCKET.LAT.009` · CloudColony Triple Protocol  
**Protocol ID:** `MEDINA-SUBAGENT-MESH/1.0` (alias **MSMP-1.0**)  
**Always-use hook:** `pocket.agent_hook.ensure_mesh_hook()` — armed on every `serve()`  
**Runtime modules:** `pocket.agent_hook` · `pocket.protocols.subagent_mesh_protocol` · `pocket.mesh_disk` · `pocket.subagent_dispatch` · `pocket.design_agents` · `pocket.hz_mesh` · `pocket.protocols.*`  
**API:** `GET /v1/protocols/mesh` · `POST /v1/hooks/mesh` · `POST /v1/subagents/dispatch`  
**Operator doc:** `docs/SUBAGENT_MESH.md` · Companion notes: `POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL_NOTES.md` · PDF sibling

---

## 1. Executive Summary

This report formalizes the **POCKET Subagent Mesh**: an Antigravity-style coordination fabric in which named workers **message and leave artifacts without sharing a chat transcript**. The mesh is not a second chat product; it is a **host-local protocol layer** that decouples agent work from the conversational UI while remaining callable from the same desk (composer `@mentions`, HTTP `/v1/*`, orchestrator skills).

At the storage and crypto layer, the mesh prefers a high-capacity volume root (`E:\POCKET_MESH` when writable; else `D:\POCKET_MESH`; else `~/.pocket/mesh`). Identity is **SHA-256(salt ∥ agent_id)**. Envelopes are **HMAC-SHA256** signed; message bodies may be sealed with the stdlib-only body cipher **`hmac-sha256-xor-v1`**. Coordination buses are **frequency channels** (`channels/freq-N.jsonl`), optionally mapped from BLE-style MHz markers.

Formally, the doctrine that operators and integrators must always prefer mesh coordination over stuffing multi-agent work into a single chat thread is named:

> **MEDINA Subagent Mesh Protocol (MSMP-1.0)** — always-use doctrine for multi-agent work on POCKET hosts.

**CloudColony** is treated as the **framework / ecosystem wrap** (Triple Protocol, colony MCP stack, optional ICP bridge). **POCKET** (and **MESIE** as compute lane) are **product builds** that implement and demo MSMP on a real Windows operator machine. This report separates measured host reality from planned cross-colony federation.

### Realization snapshot (2026-07-28)

| Claim | Status |
|-------|--------|
| Virtual mesh root on `E:\POCKET_MESH` | **Live** — write-probed at import |
| Latin (12) + Design (4) + Headless (4) identities | **Live** — registered under `agents/` |
| HMAC envelopes + body_cipher | **Live** — `mesh_disk.send_message` |
| `@dispatch` + `/v1/subagents/*` + `/v1/mesh/*` | **Live** — `server.py` routes |
| Design specialists leave critique + CSS on mesh | **Live** — artifacts under DESIGN/AESTHETE/LAYOUT |
| Headless pack heartbeats on `freq-1` | **Live** — heartbeats + worker scripts on `E:\…\workers` |
| Physical BLE radio mesh | **Planned** — file-bus default; BLE map stubs only |
| Cross-host CloudColony federation of mesh mail | **Planned** — Triple Protocol bridge, not required for local beta |
| Published multi-host latency / throughput benchmarks | **Planned** — not claimed as measured here |

---

## 2. Problem: Chat-Coupled Agents vs Antigravity-Style Mesh

### 2.1 Failure mode of chat-coupled multi-agent systems

Most “multi-agent” demos remain **chat-coupled**:

1. A single transcript is the only shared memory.  
2. Specialist “agents” are prompt roles, not durable identities with mailboxes.  
3. Side effects (files, screenshots, critiques) are buried in assistant turns.  
4. Parallel work collides: one agent’s verbosity starves another’s context window.  
5. Security is all-or-nothing: anyone who can read the chat can read every intermediate secret.

This pattern optimizes for **demo monologue**, not for **operator infrastructure**.

### 2.2 Antigravity-style mesh (target behavior)

An Antigravity-style mesh inverts the defaults:

| Property | Chat-coupled | Mesh (MSMP) |
|----------|--------------|-------------|
| Shared memory | Transcript | Artifacts + inboxes + channels |
| Identity | Display name in prompt | SHA-256 agent id + role |
| Work product | Message text | Signed files under agent home |
| Parallelism | Serialized turns | Independent workers + headless pulses |
| Operator view | Scrollback | Roster + channel tail + dispatch chips |
| Host I/O | Optional tool call | First-class (UIA, vdisk, workers on E:) |

POCKET implements this on the **operator host**, not as a cloud multi-tenant chat SaaS. The desk UI remains the **intake plane**; the mesh is the **execution and coordination plane**.

### 2.3 Why this matters for funders and beta users

- **Fundable demos** need reproducible artifacts (checklists, CSS snippets, RFE briefs), not only witty chat.  
- **Beta operators** need to see *which agent* did *what* on *which bus*, including when the LLM is offline.  
- **Framework positioning** (CloudColony) requires a host-local proof that agents are more than roles in a prompt template.

---

## 3. Architecture

### 3.1 Logical stack

```
[Operator / Phone / Composer]
        │  @MENTION  ·  POST /v1/subagents/dispatch  ·  orchestrator skill
        ▼
[MEDINA Subagent Mesh Protocol — MSMP-1.0]
        │
        ├─ Identity ………… agent_sha = SHA-256(mesh_salt || AGENT_ID)
        ├─ Mail …………… agents/<ID>/{inbox,outbox,artifacts,keys}
        ├─ Channels ……… channels/freq-N.jsonl  (Hz lanes)
        ├─ Crypto ………… HMAC-SHA256 envelope + optional body_cipher
        ├─ VDisk …………… vdisk/workspaces/<ID>/  (logical, not OS VHD)
        └─ Workers ……… workers/worker_*.py on mesh root (E: preferred)
        │
        ├─ Microsoft protocol  → UIA / desktop / page render
        ├─ Bluetooth/Hz protocol → MHz → freq-N mapping (file-bus)
        └─ Headless pack  → background heartbeats + offload scripts
```

### 3.2 E: virtual mesh disk

**Module:** `pocket.mesh_disk`

Root selection order:

1. `POCKET_MESH_ROOT` environment override  
2. `E:/POCKET_MESH` (preferred multi-TB class volume)  
3. `D:/POCKET_MESH`  
4. `~/.pocket/mesh`

The “virtual disk” is a **logical workspace tree** under `…/vdisk`, **not** a mounted OS `.vhd`. Goals:

- Isolate agent I/O onto high-capacity storage  
- Keep C: free of agent mail noise  
- Let headless Python workers write files independently of chat  
- Provide a stable path for demos and backups (`E:\POCKET_MESH`)

| Path | Purpose |
|------|---------|
| `E:\POCKET_MESH` | Mesh root (when E: is writable) |
| `agents/<ID>/inbox\|outbox\|artifacts\|keys` | Per-agent mailbox |
| `channels/freq-N.jsonl` | Frequency buses |
| `vdisk/workspaces/<ID>/` | Per-agent file offload |
| `vdisk/shared/` | Shared workspace |
| `workers/*.py` | Headless offload scripts |
| `protocols/{microsoft,bluetooth,hz}/` | Protocol READMEs written at bootstrap |
| `artifacts/` | Global artifact index copies |
| `.mesh_salt` | 32-byte salt for identity + HMAC key material |

### 3.3 SHA identities

```text
agent_sha(agent_id) = SHA-256( salt_bytes || utf8(agent_id) )
```

Each `ensure_agent` writes `agents/<ID>/id.json` containing `id`, `sha256`, `role`, `home`, `mesh`. SHA prefixes appear in send receipts (`from_sha` / `to_sha` truncated in API responses). Identity is **host-local** (bound to mesh salt); cross-host federation would re-bind or re-attest under CloudColony bridge rules (**planned**).

### 3.4 HMAC + body cipher

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Integrity | HMAC-SHA256 over canonical JSON core (sorted keys) | **Live** |
| Compare | `hmac.compare_digest` on verify | **Live** |
| Body privacy | `hmac-sha256-xor-v1` keystream XOR (stdlib only) | **Live** |
| Nonce | 16 random bytes per encrypt | **Live** |
| Channel log | Same envelope; body field shows `[encrypted]` when sealed | **Live** |
| AES-GCM / multi-host key exchange | — | **Planned** |

Envelope core fields (signed): `id`, `from`, `from_sha`, `to`, `to_sha`, `kind`, `body`, `body_cipher`, `artifact`, `channel`, `at`. Signature field: `hmac_sha256`.

**Scope note:** This protects mesh mail integrity/privacy on the operator host relative to casual file inspection of channel logs. It is **not** a claim of multi-tenant SaaS isolation or hardware-backed enclave security.

### 3.5 Frequency channels (Hz lanes)

**Modules:** `pocket.hz_mesh`, `pocket.protocols.bluetooth_hz`

| Lane | Channel | Use |
|------|---------|-----|
| user | `freq-0` | Operator `@dispatch` |
| heartbeat | `freq-1` | Headless pulses |
| design | `freq-2` | Design bus |
| security | `freq-3` | Sentinel / audit |
| ship | `freq-4` | Release / beta |
| intel | `freq-5` | Research + BLE stubs |

BLE advertising markers map when exact MHz is supplied:

| MHz (approx BLE adv) | Channel |
|----------------------|---------|
| 2402 | `freq-0` |
| 2426 | `freq-1` |
| 2480 | `freq-2` |

Other values in 2400–2500 quantize into slots; outside band uses modular `freq-0…15`. **Physical BLE is optional**; default transport is the encrypted file-bus.

---

## 4. Agent Packs

Total core pack: **20** identities in `mesh_disk.CORE_AGENTS` (12 Latin + 4 Design + 4 Headless).

### 4.1 Latin pack (12)

| ID | Class | Role (product) |
|----|-------|----------------|
| **ARCHON** | alpha | Multimodal desk orchestrator |
| **HYDRA** | alpha | Parallel multi-job fan-out |
| **SCRUTATOR** | specialist | Research / lookup / repo inspect |
| **SCRIPTOR** | specialist | Compose drafts; leave notes |
| **PORTARIUS** | specialist | Open allow-listed host apps |
| **OCULUS** | specialist | Sense / screenshot path |
| **SPECULUM** | specialist | Screen record status / demos |
| **REPOSITOR** | specialist | Git / GitHub / storekeeping |
| **CONSILIARIUS** | specialist | Copilot paste + send paths |
| **TABELLARIUS** | specialist | Outlook draft courier |
| **NAVIGATOR** | specialist | Browser multi-step |
| **GUPPY** | alpha (kept name) | Silent commercial multi-step |

**Source of truth for Latin meanings:** `pocket.alpha_workers` · paper `POCKET_LATIN_WORKERS.md`.

### 4.2 Design pack (4)

| ID | Role | Focus |
|----|------|-------|
| **DESIGN** | Lead product design | Cohesion, nav, hierarchy, ship polish |
| **AESTHETE** | Visual taste | Color, type, contrast, density |
| **LAYOUT** | Structure | Grid, spacing, rails, breakpoints |
| **MOTION** | Motion + feedback | Transitions, toasts, reduced-motion |

**Module:** `pocket.design_agents`  
**Doctrine:** DESIGN is **first-class** (`role=design`). It is **not** aliased to SCRIPTOR. Dispatch aliases such as `@UI` / `@UX` → DESIGN; `@GRID` → LAYOUT; `@ANIMATION` → MOTION.

Design agents leave:

- Critique markdown artifacts  
- CSS snippet artifacts  
- Virtual disk copies under `vdisk/workspaces/<ID>/design/`  
- Status on `freq-2` (design) and notify SHIP on `freq-4`

### 4.3 Headless pack (4)

| ID | Purpose | E: worker script |
|----|---------|------------------|
| **FORGE_HEADLESS** | Build / test / package | `workers/worker_forge.py` |
| **SENTINEL_HEADLESS** | Security + sanity + audit | `workers/worker_sentinel.py` |
| **RESEARCH_HEADLESS** | Research packs + RFE sense notes | `workers/worker_research.py` |
| **SHIP_HEADLESS** | Release / beta checklist + demos | `workers/worker_ship.py` |

Headless agents:

1. Register with `role=headless`  
2. Optionally pulse every ~120s (`start_headless_pack`) with heartbeat artifacts + `freq-1` messages  
3. Offload to E: Python workers via subprocess when dispatched  
4. Notify ARCHON on completion / heartbeat  

---

## 5. MEDINA Subagent Mesh Protocol (MSMP-1.0)

### 5.1 Formal name

| Field | Value |
|-------|--------|
| **Name** | MEDINA Subagent Mesh Protocol |
| **Short** | MSMP-1.0 |
| **Lab** | Medina Tech Labs / ItsNotAI Labs |
| **Host realization** | POCKET `2.x` mesh disk + dispatch |
| **Always-use doctrine** | Multi-agent work **must** prefer mesh mail + artifacts over transcript stuffing |

### 5.2 Always-use doctrine (normative)

Operators, desk UI, and automated planners **SHALL**:

1. **Address agents by stable ID** (`@DESIGN`, `@OCULUS`, …), not free-form role paragraphs.  
2. **Dispatch via MSMP** (`POST /v1/subagents/dispatch` or orchestrator `subagents_dispatch`) so mail, HMAC, and artifacts are produced.  
3. **Leave work products as artifacts** under the agent home (and vdisk when files are large).  
4. **Use frequency lanes by purpose** (user / heartbeat / design / security / ship / intel).  
5. **Prefer E: mesh root** when available; do not dump agent mail onto C: user profiles.  
6. **Bootstrap before demo** (`POST /v1/mesh/bootstrap` or `GET /v1/mesh`) so the 20-pack exists.  
7. **Keep chat as intake**, not as the sole store of multi-agent results.

Operators **SHALL NOT**:

1. Alias DESIGN → SCRIPTOR.  
2. Claim physical BLE or multi-host encryption beyond what is implemented.  
3. Treat HMAC mesh mail as a substitute for host auth on HTTP routes.  
4. Publish fabricated latency/throughput numbers as measured.

### 5.3 Message lifecycle

```
USER (or peer)
  → send_message / dispatch
  → ensure_agent(from), ensure_agent(to)
  → encrypt body (default)
  → sign envelope
  → write recipient inbox + sender outbox
  → append channel jsonl
  → optional host skill execution (_execute_agent)
  → leave_artifact (dispatch result)
  → notify ARCHON (status)
```

### 5.4 Always-use hook (`pocket.agent_hook`) — **live**

**Module:** `pocket.agent_hook` · **Protocol constants:** `pocket.protocols.subagent_mesh_protocol` (`MEDINA-SUBAGENT-MESH/1.0`)

| Function | Behavior |
|----------|----------|
| `ensure_mesh_hook()` | Idempotent arm: bootstrap core + design + 4 headless |
| `route_message(text)` | Parse `@` → mesh `dispatch` |
| `dispatch_named(agent, msg)` | Explicit agent without chat |
| `protocol_report()` | Ops/research snapshot for API |

**Host:** `server.serve()` calls `ensure_mesh_hook()` before accepting traffic. Banner: `MESH: MEDINA-SUBAGENT-MESH/1.0`.

| Hook site | Module | Behavior |
|-----------|--------|----------|
| Host start | `pocket.server.serve` | Always arm hook |
| HTTP protocol | `GET /v1/protocols/mesh` | `protocol_report()` |
| Force re-arm | `POST /v1/hooks/mesh` | `ensure_mesh_hook(force=True)` |
| Composer `@` | `pocket.app_ui` | `POST /v1/subagents/dispatch` |
| HTTP dispatch | `pocket.server` | Hook arm + `dispatch` |
| Panel roster | `pocket.subagents_panel` | Latin + design + headless + mesh |
| Design pack | `pocket.design_agents` | Critique / CSS / vdisk |

**Env:** `POCKET_MESH_HOOK`, `POCKET_ALWAYS_MESH`, `POCKET_HEADLESS_AUTO`, `POCKET_MESH_ROOT`.

---

## 6. CloudColony Framework Wrap vs Product Build (POCKET / MESIE)

### 6.1 Definitions

| Layer | What it is | Example artifacts |
|-------|------------|-------------------|
| **Framework wrap (CloudColony)** | Ecosystem protocols, MCP colony stack, optional ICP bridge, product narrative at CloudColony.io | Triple Protocol, vault/compute/fleet MCP, colony bridge |
| **Product build (POCKET)** | Operator host OS: desk, orchestrator, mesh, UIA, phone intake | `pocket-os`, `E:\POCKET_MESH`, `/v1/*` |
| **Product / compute lane (MESIE)** | Spectral / virtual processor / edge compute workspace | MESIE repo, edge :8750 (ecosystem), POCKET workspace id `mesie` |

### 6.2 Separation of concerns

```
CloudColony (framework wrap)
  ├── Triple Protocol (P1 Loom · P2 MCP Colony · P3 Bridge)
  ├── Colony products / ICP federation (optional)
  └── Narrative + beta promoter surface
           │
           │  “implements / demos”
           ▼
POCKET (product build on operator host)
  ├── MSMP mesh disk + Latin/Design/Headless packs
  ├── Microsoft + Bluetooth/Hz protocols (host + file-bus)
  └── Desk + phone + orchestrator
           │
           │  “compute workspace / lane”
           ▼
MESIE (engine / compute product)
  └── Embed, match, virtual processor, benchmarks (where installed)
```

**Rule for this paper:** POCKET’s live claims are about **host MSMP**. CloudColony claims about federation, ICP, or multi-device colony economics are **framework-level** and must be cited from CloudColony deliverables, not assumed proven by `E:\POCKET_MESH` alone.

### 6.3 Ship checklist coupling

`SHIP_HEADLESS` includes explicit beta items:

- Mesh virtual disk on E:  
- Design agents DESIGN/AESTHETE/LAYOUT/MOTION  
- Protocols microsoft + bluetooth + hz  
- **CloudColony framework repo**  
- Subagents `@` dispatch  

That checklist is **operational glue**: product ship readiness includes knowing where the framework repo lives, without requiring ICP mainnet for local demos.

---

## 7. Triple Protocol Relation

CloudColony’s **Triple Protocol** (ecosystem) is three Medina-named layers:

| ID | Name | Role |
|----|------|------|
| **P1** | MEDINA-LOOM/0.1 | Sovereign memory, multi-AI council, cross-agent signal bus |
| **P2** | MEDINA-MCP-COLONY-DEPLOY/1.0 | Deployable MCP stack — vault, compute, fleet |
| **P3** | MEDINA-COLONY-BRIDGE/1.0 | Airgap local ICP proofs + optional Capsula federation |

**MSMP-1.0** is the **POCKET host mesh protocol**. Relation:

| Concern | MSMP (POCKET) | Triple Protocol (CloudColony) |
|---------|---------------|-------------------------------|
| Agent mail | File-bus HMAC envelopes on E: | Loom signal / vault (P1) |
| Dispatch | `/v1/subagents/dispatch` | MCP vault/fleet multi-AI dispatch (P2) |
| Compute offload | Headless + vdisk workers | Compute MCP → edge MESIE (P2) |
| Federation | **Not required** for local beta | Colony Bridge → optional mainnet (P3) |
| Always-use | Multi-agent on host | Edge-first, airgap default |

**Mapping (conceptual, not a runtime dependency):**

- MSMP channels ≈ Loom signal bus at host granularity  
- Mesh agent SHA ≈ local identity prior to colony attestation  
- Headless workers ≈ edge workers before MCP packaging  
- SHIP_HEADLESS checklist ≈ beta gate before promoter demos  

**Status:** Triple Protocol implementation lives under the CloudColony / MESIE sovereign tree. POCKET **wraps and demos** the host side; full stack federation is **planned** relative to pure POCKET alpha.

---

## 8. Microsoft + Bluetooth / Hz Protocols

### 8.1 Microsoft host protocol

**Modules:** `pocket.protocols.microsoft_protocol` (canonical) · `pocket.ms_protocol` (shim)

Thin, **safe** hooks into host surfaces. No free-form PowerShell. Actions route through existing constrained modules (`desktop`, `ui_click`, `page_renderer`, `perception`, `sanity.guard_shell`).

| Hook | Purpose |
|------|---------|
| `open_host_app` / `list_host_apps` | Allow-listed apps |
| `click_ui` / `maximize_window` / `close_foreground` / `scroll_ui` | UIA / window |
| `render_page` / `find_symbols` / `sense_ui` | Page map + perception |
| `safe_shell_echo` | Sanity probe only |
| `invoke` / `run` | Named action dispatcher |

Used by PORTARIUS / OCULUS / SPECULUM / design agents when host glass is required.

### 8.2 Bluetooth / Hz protocol

**Module:** `pocket.protocols.bluetooth_hz` · façade `pocket.hz_mesh`

| API | Purpose |
|-----|---------|
| `channel_for_hz` / `hz_for_channel` | MHz ↔ `freq-N` |
| `mesh_broadcast` | Signed message on lane |
| `mesh_leave` | Artifact + optional channel announce |
| `tune` | Register interest artifact on a lane |
| `bluetooth_stub_scan` (hz_mesh) | Stub device scan → intel artifact |

**Measured:** file-bus channel publish/listen and MHz mapping functions.  
**Planned:** physical BLE device discovery bound to agent SHA + lane.

### 8.3 Protocol docs on mesh

Bootstrap writes READMEs under:

- `E:\POCKET_MESH\protocols\microsoft\`  
- `E:\POCKET_MESH\protocols\bluetooth\`  
- `E:\POCKET_MESH\protocols\hz\`  

---

## 9. API Surface

### 9.1 Subagents

| Method | Path | Body / query | Behavior |
|--------|------|--------------|----------|
| GET | `/v1/subagents` | — | Unified roster (Latin + design + headless + dynamic) + `mesh` status |
| GET | `/v1/subagents/running` | — | Running view |
| POST | `/v1/subagents/dispatch` | `{message, name?, agents?, from?, channel?}` | Parse `@mentions`, send mesh mail, execute, leave artifact |
| POST | `/v1/agents/dispatch` | same | Alias of dispatch |

**Example**

```http
POST /v1/subagents/dispatch
Content-Type: application/json

{
  "message": "@DESIGN polish composer focus ring",
  "name": "DESIGN",
  "channel": "freq-0"
}
```

Composer: type `@` for autocomplete (Latin + design + headless). Soft-fails if route missing; session message may still carry work.

### 9.2 Mesh

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/v1/mesh` | Bootstrap core agents + return `mesh_disk.status()` |
| POST | `/v1/mesh/bootstrap` | Bootstrap + start headless pack |
| POST | `/v1/mesh/send` | Raw `send_message` (from/to/body/channel/kind) |
| GET | `/v1/mesh/inbox/{agent}` | Read inbox (decrypt body_cipher → `body_plain` when valid) |
| GET | `/v1/mesh/channel?name=freq-0` | Tail channel jsonl |

### 9.3 Headless

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/v1/headless/start` | Same as bootstrap path: register + start pack |
| POST | `/v1/headless/stop` | Signal stop events for headless threads |

Interval default: **120s** (body `interval` override).

### 9.4 Orchestrator skills (non-HTTP entry)

| Skill id | Action |
|----------|--------|
| `subagents_list` | Panel list |
| `subagents_dispatch` / `dispatch` / `mention` | Dispatch |
| `mesh_bootstrap` / `headless_start` | Bootstrap + headless |

---

## 10. Empirical Status — What Is Live on `E:\POCKET_MESH`

Observations from the operator host mesh tree (archival date **2026-07-28**). These are **filesystem / code facts**, not synthetic load-test scores.

### 10.1 Live (observed)

| Item | Evidence |
|------|----------|
| Root | `E:\POCKET_MESH` with `vdisk/VIRTUAL_DISK.md` |
| Agent homes | ARCHON, HYDRA, SCRUTATOR, SCRIPTOR, PORTARIUS, OCULUS, SPECULUM, REPOSITOR, CONSILIARIUS, TABELLARIUS, NAVIGATOR, GUPPY, DESIGN, AESTHETE, LAYOUT, MOTION, FORGE/SENTINEL/RESEARCH/SHIP `_HEADLESS`, USER |
| Design artifacts | Critique + CSS under DESIGN, AESTHETE, LAYOUT; global index copies under `artifacts/` |
| Headless heartbeats | Multiple `heartbeat.md` files; outbox traffic on headless agents |
| FORGE results | `forge_result.md` + `vdisk/workspaces/FORGE_HEADLESS/forge_task.md` |
| SHIP checklists | `SHIP_CHECKLIST.md` artifacts |
| Channels present | `freq-0.jsonl`, `freq-1.jsonl`, `freq-2.jsonl`, `freq-4.jsonl` |
| Encrypted envelopes | Inbox JSON with `body: "[encrypted]"`, `body_cipher.alg = hmac-sha256-xor-v1`, `hmac_sha256` |
| Workers on E: | `worker_forge.py`, `worker_sentinel.py`, `worker_research.py`, `worker_ship.py`, `worker_design.py`, base libs |
| Protocol READMEs | `protocols/microsoft|bluetooth|hz/README.md` |
| ARCHON inbox volume | Large (100+ message files observed) — mesh is actively used |

### 10.2 Partial / soft

| Item | Note |
|------|------|
| `freq-3` / `freq-5` files | May be absent until first security/intel publish |
| MOTION artifacts | Identity exists; fewer artifacts than DESIGN/LAYOUT in sampled tree |
| Physical BLE | Stub / map only |
| Cross-process worker daemons | Subprocess on dispatch + in-process headless threads; not a separate supervised service fabric |

### 10.3 Planned (explicit non-claims)

| Item | Note |
|------|------|
| AES-256-GCM multi-host transport | Roadmap only |
| BLE device → agent SHA binding | Roadmap only |
| CloudColony ICP federation of mesh mail | Framework path; not proven by local tree |
| Published p50 dispatch latency, msgs/sec, multi-TB soak | **Not measured in this report** — do not invent |
| Standalone `agent_hook` module | **Live** — `pocket.agent_hook` + `serve()` arm |

### 10.4 Status table (measured vs planned)

| Capability | Class |
|------------|--------|
| Mesh root pick E/D/home | **Measured** (code + live E: tree) |
| 20-agent bootstrap | **Measured** |
| HMAC + xor body cipher envelopes | **Measured** (sample inbox) |
| `@dispatch` execution paths | **Measured** (artifacts + code paths) |
| Design bus `freq-2` | **Measured** |
| Headless heartbeats `freq-1` | **Measured** |
| E: worker scripts | **Measured** |
| Microsoft protocol hooks | **Measured** (module + allow-listed desktop stack) |
| BLE MHz mapping functions | **Measured** (unit logic) |
| BLE radio scan | **Planned** |
| Multi-host mesh sync | **Planned** |
| Formal benchmark suite | **Planned** |

---

## 11. Viral / Funding Framing: Frameworks + Demos + Benchmarks

### 11.1 Positioning triad

| Asset | Role in narrative |
|-------|-------------------|
| **Framework** | CloudColony Triple Protocol + MSMP doctrine — “protocols are the intelligence” |
| **Demos** | `@DESIGN` polish → artifacts; `@SHIP_HEADLESS` checklist; `@RESEARCH_HEADLESS` + RFE; SPECULUM recordings |
| **Benchmarks** | Only publish **measured** host metrics; label **planned** targets separately |

### 11.2 Demo scripts (honest)

1. **Mesh bootstrap** — `GET /v1/mesh` → show `mesh_root: E:\POCKET_MESH`, agent_count ≥ 20.  
2. **Design dispatch** — `@DESIGN polish composer` → open critique + CSS on E:.  
3. **Headless pulse** — `POST /v1/headless/start` → `freq-1` growth + heartbeat.md.  
4. **Sense path** — `@OCULUS` / `@RESEARCH_HEADLESS` → brief + optional RFE materialize.  
5. **Ship gate** — `@SHIP_HEADLESS` → checklist including CloudColony framework repo.

### 11.3 What funders should underwrite

- Host-local multi-agent **infrastructure** (mail, crypto, vdisk), not chat UX alone.  
- Named agent IP (Latin pack) as product surface.  
- Framework wrap path into CloudColony without forcing cloud dependency for beta.  
- Measured demo artifacts that can be audited on disk.

### 11.4 What not to over-claim

- “Encrypted multi-agent cloud mesh” without P3 bridge proof.  
- “BLE mesh network” without radio.  
- Latency leaderboards without a published harness.  
- MESIE spectral numbers from other papers unless re-measured in this stack.

---

## 12. Open Research Questions

1. **Key hierarchy** — Per-agent keys under `agents/<ID>/keys/` vs single mesh salt: rotation, compromise recovery, export to colony attestation.  
2. **Cipher upgrade** — When to move from `hmac-sha256-xor-v1` to AES-GCM while remaining stdlib-friendly for offline demos.  
3. **Channel GC / compaction** — jsonl growth on multi-day headless pulses; indexing vs full rewrite.  
4. **Scheduling** — Headless threads vs true process supervisors vs job queue (`pocket.jobs`) unification.  
5. **Conflict model** — Multiple writers to shared vdisk paths; last-write vs CRDT-lite.  
6. **BLE binding** — Device ID → agent SHA → lane without leaking identity on RF.  
7. **MSMP ↔ Loom signal** — Schema adapter so host envelopes become P1 signals without double-storage.  
8. **Phone parity** — Full `@dispatch` roster UX on product phone shell vs desktop composer.  
9. **Benchmark harness** — Define fixed dispatch suite (design, forge, sense, ship) with p50/p95 wall time and artifact size.  
10. **`agent_hook` package** — Single module that all UI/orchestrator paths import, with policy tests for always-use doctrine.  
11. **Multi-seat** — Two operator machines sharing mesh via tunnel without violating airgap defaults.  
12. **RBAC** — HTTP auth vs mesh envelope trust; prevent local process A from forging process B’s agent id without salt.

---

## 13. Module & File Map

### 13.1 Python modules (POCKET)

| Module | Responsibility |
|--------|----------------|
| `pocket.mesh_disk` | Root pick, SHA identity, HMAC, body cipher, mail, vdisk, bootstrap, status |
| `pocket.subagent_dispatch` | `@mention` parse, dispatch, headless pack, E: worker invoke |
| `pocket.design_agents` | DESIGN / AESTHETE / LAYOUT / MOTION |
| `pocket.subagents_panel` | Unified roster for desk UI |
| `pocket.hz_mesh` | Logical Hz lanes + publish/listen |
| `pocket.ms_protocol` | Shim → microsoft protocol |
| `pocket.protocols.microsoft_protocol` | Host UIA/desktop/page hooks |
| `pocket.protocols.bluetooth_hz` | MHz ↔ channel, broadcast/leave/tune |
| `pocket.protocols` | Package exports |
| `pocket.alpha_workers` | Latin worker registry + runners |
| `pocket.orchestrator_exec` | Skills: dispatch, mesh bootstrap |
| `pocket.app_ui` | Composer `@` + `/v1/subagents` UI |
| `pocket.server` | HTTP surface §9 |
| **agent_hook (surface)** | Call sites above; discrete module **planned** |

### 13.2 Docs

| Path | Role |
|------|------|
| `docs/SUBAGENT_MESH.md` | Short operator mesh doc |
| `docs/research/POCKET_LATIN_WORKERS.md` | Latin naming paper |
| `docs/research/RFE_v1_Architectural_Synthesis.md` | Style / RFE peer paper |
| This file | Full MSMP + CloudColony wrap report |
| `…_NOTES.md` | Beta operator checklist |

### 13.3 Live tree (host)

| Path | Role |
|------|------|
| `E:\POCKET_MESH\agents\*` | Mailboxes |
| `E:\POCKET_MESH\channels\freq-*.jsonl` | Buses |
| `E:\POCKET_MESH\workers\worker_*.py` | Headless offload |
| `E:\POCKET_MESH\vdisk\` | Logical virtual disk |
| `E:\POCKET_MESH\protocols\` | Protocol notes |

### 13.4 External framework (CloudColony)

| Path / concept | Role |
|----------------|------|
| CloudColony sovereign README | Triple Protocol entry |
| `mesie.cloud.triple_protocol` | P1/P2/P3 layer definitions |
| MESIE workspace (executor `mesie` id) | Compute product lane |

---

## 14. Conclusion

POCKET’s subagent mesh is a **measured host protocol**, not a slide deck:

- **MSMP-1.0** codifies always-use mesh coordination.  
- **E:\POCKET_MESH** is live with identities, encrypted mail, design artifacts, and headless workers.  
- **Microsoft + Hz/Bluetooth** protocols ground agents in OS truth and frequency-addressable buses.  
- **CloudColony** is the framework wrap; **POCKET / MESIE** are product builds that make the doctrine demoable without requiring federation for beta.

The correct funder and beta narrative is: **frameworks define the laws; demos leave artifacts on the mesh; benchmarks stay honest.**

---

*Document status: Authorized for technical diligence, funder packets, and beta operators.  
Archival code: `INL-2026-POCKET.MESH.v1` · 2026-07-28 · ItsNotAI Labs / Medina Tech Labs*
