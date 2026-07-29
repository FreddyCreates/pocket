# Real-world embodiment & offload (AI self-features)

Built while the operator stepped out — what **we** (Grok / Codex / Claude / WOA) asked the host for.

## Why

Chat turns are expensive. Real-world work (open app, screenshot, multi-step desk) should **not** hold the model hostage.  
Agents need a place to **queue** work, **prove** it happened, and **remember** how to do it again.

## Surfaces

| Piece | Path / API | Role |
|-------|------------|------|
| Offload queue | `POST /v1/offload` · mode `offload` | Background multi-step jobs + ticket |
| Embodiment | `POST /v1/embodiment/run` | Sync short plan: caps · screenshot · apps · files |
| Capability map | `GET /v1/capabilities` | Live “what can we do now” |
| Task market | `POST /v1/task-market/post` · claim | Swarm job board on bus |
| Proof packs | `~/.pocket/proofs/` | JSON + PROOF.md per run |
| Skill memory | `learn.record_run` | Successful offloads → learned skills |
| Agent bus | `freq-coding` | Hashed handoffs (already existed) |

## Desk

- New agent button: **Offload**  
- Right rail: **Offload · real world** ticket list  
- AI workspace inject includes capability snip + offload tip  

## Example

```http
POST /v1/offload
{"goal":"snapshot capabilities, screenshot, note: ship-day desk check","agent":"GROK"}
```

```http
GET /v1/offload/off-xxxxxxxxxxxx
```

## Swarm decision (bus)

We posted `AI_SELF_FEATURES_MANIFEST.md` from GROK → CODEX/ARCHON:

1. Offload queue  
2. Embodiment toolkit  
3. Capability map  
4. Skill memory  
5. Proof packs  
6. Task market  

All six landed in code.

## Safety

- App allowlist + path roots for file peek  
- No live money paths  
- Shell still goes through existing safety  
- Background worker is daemon thread inside host process  
